import argparse
import sys
import json
import logging
import traceback
from typing import Optional
from config import settings
from app.logging_setup import setup_logging
from app.workflows.generate_protocols import GenerateProtocolsWorkflow
from app.workflows.log_observation import LogObservationWorkflow
from app.workflows.reflect_observation import ReflectObservationWorkflow
from app.workflows.build_report import BuildReportWorkflow
from app.services.qdrant import QdrantService
from app.services.validation import validate_json_file
from app.services.export import Exporter
from app.models.enums import ProtocolStatus
from app.models.protocol import PraxisProtocol, ProtocolDraft
from app.models.reflection import PraxisReflection
from app.models.failure import FailureRecord

logger = logging.getLogger(__name__)

def main(args_list: Optional[list[str]] = None) -> None:
    parser = argparse.ArgumentParser(
        description="Praxis CLI: Embodied Experiment Layer for Keystone Propositions."
    )
    
    # Global options
    parser.add_argument("--dry-run", action="store_true", help="Perform no Qdrant writes or file writes.")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose debug logging.")
    parser.add_argument("--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR"], help="Override logging level.")
    parser.add_argument("--workers", type=int, help="Override parallel workers count.")

    subparsers = parser.add_subparsers(dest="command", required=True, help="Subcommand to execute")

    # Command: probe
    subparsers.add_parser("probe", help="Inspect Qdrant database collections and verify connections.")

    # Command: classify
    classify_parser = subparsers.add_parser("classify", help="Assess candidate actionability without generating protocols.")
    classify_parser.add_argument("--limit", type=int, default=0, help="Max candidates to classify.")
    classify_parser.add_argument("--keystone-id", help="Classify a specific keystone ID.")
    classify_parser.add_argument("--min-convergence", type=float, help="Min convergence filter.")

    # Command: generate
    gen_parser = subparsers.add_parser("generate", help="Run the full workflow to generate and save protocols.")
    gen_parser.add_argument("--limit", type=int, default=0, help="Max candidates to generate.")
    gen_parser.add_argument("--keystone-id", help="Generate protocol for a specific keystone ID.")
    gen_parser.add_argument("--min-convergence", type=float, help="Min convergence filter.")

    # Command: list
    list_parser = subparsers.add_parser("list", help="List stored items from collections.")
    list_subparsers = list_parser.add_subparsers(dest="target", required=True, help="Collection type to list")
    
    # list protocols
    list_proto_parser = list_subparsers.add_parser("protocols", help="List generated protocols.")
    list_proto_parser.add_argument("--status", choices=[s.value for s in ProtocolStatus], help="Filter by status.")
    
    # list register
    list_subparsers.add_parser("register", help="List Appendix A Refused/Non-Actionable Register entries.")
    
    # list feedback
    list_subparsers.add_parser("feedback", help="List compiled reflections and feedback recommendations.")

    # Command: show
    show_parser = subparsers.add_parser("show", help="Display details of a specific item.")
    show_subparsers = show_parser.add_subparsers(dest="show_target", required=True, help="Item type to show")
    
    # show protocol
    show_proto_parser = show_subparsers.add_parser("protocol", help="Show full JSON payload of a protocol.")
    show_proto_parser.add_argument("protocol_id", help="UUID of the protocol.")
    
    # show reflection
    show_ref_parser = show_subparsers.add_parser("reflection", help="Show full JSON payload of a reflection.")
    show_ref_parser.add_argument("reflection_id", help="UUID of the reflection.")

    # Command: validate
    val_parser = subparsers.add_parser("validate", help="Validate a local JSON payload against schema.")
    val_subparsers = val_parser.add_subparsers(dest="val_target", required=True, help="Schema type to validate")
    
    # validate protocol
    val_proto = val_subparsers.add_parser("protocol", help="Validate protocol JSON file.")
    val_proto.add_argument("file", help="Path to the JSON file.")

    # Command: log-observation
    log_parser = subparsers.add_parser("log-observation", help="Submit observation JSON file for a protocol.")
    log_parser.add_argument("--protocol-id", help="Target Protocol UUID. Optional, auto-resolved when omitted.")
    log_parser.add_argument("--file", required=True, help="Path to the observation JSON file.")

    # Command: reflect
    ref_parser = subparsers.add_parser("reflect", help="Generate qualitative reflection for an observation.")
    ref_parser.add_argument("--observation-id", help="Target Observation UUID. Optional, auto-resolved when omitted.")

    # Command: export
    exp_parser = subparsers.add_parser("export", help="Export a Qdrant collection to a JSON file.")
    exp_parser.add_argument("export_target", choices=["protocols", "observations", "reflections"], help="Target collection.")
    exp_parser.add_argument("--out", required=True, help="Output path (e.g. data/protocols.json).")

    # Command: report
    rep_parser = subparsers.add_parser("report", help="Compile and generate the Report Book.")
    rep_parser.add_argument("--out", required=True, help="Output Markdown file path.")
    rep_parser.add_argument("--pdf", action="store_true", help="Also render a paginated PDF version.")
    rep_parser.add_argument("--html", action="store_true", help="Also render a hyperlinked HTML version.")
    rep_parser.add_argument("--run-id", help="Filter by run ID.")
    rep_parser.add_argument("--since", help="Filter since ISO date.")
    rep_parser.add_argument("--from-exports", help="Compile using local JSON exports directory instead of Qdrant.")
    rep_parser.add_argument("--index-terms", help="Path to index keywords text file.")
    rep_parser.add_argument("--title", help="Custom report title.")

    # Parse arguments
    parsed_args = parser.parse_args(args_list)

    # Apply configuration overrides
    if parsed_args.dry_run:
        settings.dry_run = True
    if parsed_args.workers:
        settings.praxis_workers = parsed_args.workers
    if parsed_args.log_level:
        settings.log_level = parsed_args.log_level
    elif parsed_args.verbose:
        settings.log_level = "DEBUG"

    # Setup Logging
    setup_logging(
        log_level=settings.log_level,
        log_json=settings.log_json
    )

    logger.info("Praxis CLI started.")
    if settings.dry_run:
        logger.info("DRY RUN mode is ACTIVE. No data will be written.")

    debug_mode = settings.log_level == "DEBUG"

    try:
        execute_command(parsed_args)
    except Exception as e:
        logger.exception("CLI execution failed.")
        print(f"Error: {e}", file=sys.stderr)
        if debug_mode:
            print("\nTraceback:", file=sys.stderr)
            traceback.print_exc(file=sys.stderr)
        sys.exit(1)

def execute_command(args: argparse.Namespace) -> None:
    cmd = args.command

    if cmd == "probe":
        # Run probe logic
        qdrant = QdrantService(settings)
        print("Connecting to Qdrant...")
        try:
            # Output collection details
            collections_list = qdrant.client.get_collections()
            print("Successfully connected to Qdrant.")
            print("Existing collections:")
            for col in collections_list.collections:
                info = qdrant.client.get_collection(col.name)
                print(f"- Name: {col.name}")
                print(f"  Vectors config: {info.config.params.vectors}")
                print(f"  Status: {info.status}")
                print(f"  Points count: {info.points_count}")
        except Exception as e:
            print(f"Failed to connect or query Qdrant: {e}", file=sys.stderr)
            raise
        finally:
            qdrant.close()

    elif cmd == "classify":
        # Score/classify without generating protocol drafts
        workflow = GenerateProtocolsWorkflow(settings)
        # Monkey patch or configure workflow to skip draft and safety/critic steps
        # To do this safely, we run workflow with mock generator/writer or we implement a dry classify run.
        # Override condense_practice to skip LLM condenser calls during classifiy
        def dummy_condense(record, assessment):
            # return a dummy draft
            return ProtocolDraft(
                title="Dummy", working_hypothesis="Dummy", purpose="Dummy",
                practice_mode="observation", risk_tier=0, duration_minutes=5,
                duration_days=1, frequency="once", steps=["Step 1", "Step 2", "Step 3"]
            )
        workflow.condenser.condense_practice = dummy_condense
        # Run workflow in dry_run mode
        original_dry_run = settings.dry_run
        settings.dry_run = True
        try:
            workflow.run(
                limit=args.limit,
                keystone_id=args.keystone_id,
                min_convergence=args.min_convergence
            )
        finally:
            settings.dry_run = original_dry_run

    elif cmd == "generate":
        # Full protocol generation workflow
        workflow = GenerateProtocolsWorkflow(settings)
        workflow.run(
            limit=args.limit,
            keystone_id=args.keystone_id,
            min_convergence=args.min_convergence
        )

    elif cmd == "list":
        qdrant = QdrantService(settings)
        try:
            if args.target == "protocols":
                payloads = qdrant.scroll_collection(settings.praxis_protocols_collection, limit=1000)
                protocols = [PraxisProtocol(**p) for p in payloads]
                if args.status:
                    protocols = [p for p in protocols if p.status.value == args.status]
                
                print(f"\n--- Protocols ({len(protocols)}) ---")
                print(f"{'Protocol ID':<38} | {'Title':<30} | {'Mode':<15} | {'Risk':<6} | {'Status':<10}")
                print("-" * 110)
                for p in protocols:
                    print(f"{p.protocol_id:<38} | {p.title[:30]:<30} | {p.practice_mode.value:<15} | {p.risk_tier.value:<6} | {p.status.value:<10}")

            elif args.target == "register":
                payloads = qdrant.scroll_collection(settings.praxis_failures_collection, limit=5000)
                failures = [FailureRecord(**f) for f in payloads]
                register = [f.register_entry for f in failures if f.register_entry]
                
                print(f"\n--- Appendix A Non-Actionable Register ({len(register)}) ---")
                print(f"{'Keystone ID':<25} | {'Concept':<25} | {'Stage':<15} | {'Reason':<40}")
                print("-" * 115)
                for r in register:
                    reason = r.reason[:40] if r.reason else ""
                    print(f"{r.keystone_id[:25]:<25} | {r.keystone_concept[:25]:<25} | {r.stage:<15} | {reason:<40}")

            elif args.target == "feedback":
                payloads = qdrant.scroll_collection(settings.praxis_reflections_collection, limit=1000)
                reflections = [PraxisReflection(**r) for r in payloads]
                
                print(f"\n--- Reflections & Recommendations ({len(reflections)}) ---")
                print(f"{'Reflection ID':<38} | {'Protocol ID':<38} | {'Recommendation':<30}")
                print("-" * 112)
                for r in reflections:
                    print(f"{r.reflection_id:<38} | {r.protocol_id:<38} | {r.feedback_recommendation.value:<30}")
        finally:
            qdrant.close()

    elif cmd == "show":
        qdrant = QdrantService(settings)
        try:
            if args.show_target == "protocol":
                p = qdrant.get_point_by_id(settings.praxis_protocols_collection, args.protocol_id)
                if p:
                    print(json.dumps(p, indent=2))
                else:
                    print(f"Protocol '{args.protocol_id}' not found.", file=sys.stderr)
                    sys.exit(1)
            elif args.show_target == "reflection":
                r = qdrant.get_point_by_id(settings.praxis_reflections_collection, args.reflection_id)
                if r:
                    print(json.dumps(r, indent=2))
                else:
                    print(f"Reflection '{args.reflection_id}' not found.", file=sys.stderr)
                    sys.exit(1)
        finally:
            qdrant.close()

    elif cmd == "validate":
        if args.val_target == "protocol":
            is_valid, msg = validate_json_file(args.file, "protocol")
            print(msg)
            if not is_valid:
                sys.exit(1)

    elif cmd == "log-observation":
        workflow = LogObservationWorkflow(settings)
        workflow.run(protocol_id=args.protocol_id, file_path=args.file)

    elif cmd == "reflect":
        workflow = ReflectObservationWorkflow(settings)
        workflow.run(observation_id=args.observation_id)

    elif cmd == "export":
        qdrant = QdrantService(settings)
        try:
            exporter = Exporter(qdrant, settings)
            exporter.export_collection(args.export_target, args.out)
        finally:
            qdrant.close()

    elif cmd == "report":
        workflow = BuildReportWorkflow(settings)
        workflow.run(
            output_path=args.out,
            from_exports_dir=args.from_exports,
            run_id=args.run_id,
            since=args.since,
            index_terms_path=args.index_terms,
            title=args.title,
            enable_pdf=args.pdf,
            enable_html=args.html
        )
