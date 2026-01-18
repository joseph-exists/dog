#!/usr/bin/env python3
"""
LLM Catalog CSV Loader

Loads LLM providers and models from CSV files into the database.
Uses direct database access for seeding (admin operation).

Usage:
    # Load both providers and models
    python load_catalog.py

    # Load only providers
    python load_catalog.py --providers-only

    # Load only models (providers must exist)
    python load_catalog.py --models-only

    # Clear existing data first
    python load_catalog.py --clear

    # Dry run (show what would be loaded)
    python load_catalog.py --dry-run

    # Custom CSV files
    python load_catalog.py --providers custom_providers.csv --models custom_models.csv

CSV Format:
    providers.csv: name,provider_type,description,base_url,is_enabled,is_system
    models.csv: provider_name,model_id,display_name,description,context_window,
                is_default,is_enabled,sort_order,has_vision,has_function_calling,
                has_streaming,has_json_mode
"""
import argparse
import csv
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# Add backend app to path for imports
backend_path = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(backend_path))

from sqlmodel import Session, select
from app.core.db import engine
from app.models import LLMProvider, LLMProviderType, LLMModel


def parse_bool(value: str | None) -> bool | None:
    """Parse boolean from CSV string."""
    if value is None or value.strip() == "":
        return None
    return value.strip().lower() in ("true", "1", "yes", "t")


def parse_int(value: str | None) -> int | None:
    """Parse integer from CSV string."""
    if value is None or value.strip() == "":
        return None
    return int(value.strip())


def load_providers(
    csv_path: Path,
    session: Session,
    dry_run: bool = False
) -> dict[str, LLMProvider]:
    """Load providers from CSV. Returns dict mapping name -> provider."""
    print(f"\n📂 Loading providers from: {csv_path}")

    providers = {}
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            name = row["name"].strip()
            provider_type_str = row["provider_type"].strip().upper()

            # Check if provider already exists
            existing = session.exec(
                select(LLMProvider).where(
                    LLMProvider.name == name,
                    LLMProvider.is_deleted == False
                )
            ).first()

            if existing:
                print(f"  ⏭️  Skipping '{name}' (already exists)")
                providers[name] = existing
                continue

            try:
                provider_type = LLMProviderType[provider_type_str]
            except KeyError:
                print(f"  ❌ Invalid provider_type '{provider_type_str}' for '{name}'")
                continue

            provider = LLMProvider(
                name=name,
                provider_type=provider_type,
                description=row.get("description", "").strip() or None,
                base_url=row.get("base_url", "").strip() or None,
                is_enabled=parse_bool(row.get("is_enabled", "true")),
                is_system=parse_bool(row.get("is_system", "true")),
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )

            if dry_run:
                print(f"  🔍 Would create: {name} ({provider_type.value})")
            else:
                session.add(provider)
                session.flush()  # Get the ID
                print(f"  ✅ Created: {name} ({provider_type.value}) [{provider.id}]")

            providers[name] = provider

    return providers


def load_models(
    csv_path: Path,
    session: Session,
    providers: dict[str, LLMProvider],
    dry_run: bool = False
) -> list[LLMModel]:
    """Load models from CSV."""
    print(f"\n📂 Loading models from: {csv_path}")

    models = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            provider_name = row["provider_name"].strip()
            model_id = row["model_id"].strip()
            display_name = row["display_name"].strip()

            # Find provider
            provider = providers.get(provider_name)
            if not provider:
                # Try to find in database
                provider = session.exec(
                    select(LLMProvider).where(
                        LLMProvider.name == provider_name,
                        LLMProvider.is_deleted == False
                    )
                ).first()

            if not provider:
                print(f"  ❌ Provider not found: '{provider_name}' for model '{model_id}'")
                continue

            # Check if model already exists
            existing = session.exec(
                select(LLMModel).where(
                    LLMModel.provider_id == provider.id,
                    LLMModel.model_id == model_id,
                    LLMModel.is_deleted == False
                )
            ).first()

            if existing:
                print(f"  ⏭️  Skipping '{display_name}' (already exists)")
                models.append(existing)
                continue

            model = LLMModel(
                provider_id=provider.id,
                model_id=model_id,
                display_name=display_name,
                description=row.get("description", "").strip() or None,
                context_window=parse_int(row.get("context_window")),
                is_default=parse_bool(row.get("is_default", "false")) or False,
                is_enabled=parse_bool(row.get("is_enabled", "true")),
                is_deprecated=False,
                sort_order=parse_int(row.get("sort_order")) or 0,
                has_vision=parse_bool(row.get("has_vision")),
                has_function_calling=parse_bool(row.get("has_function_calling")),
                has_streaming=parse_bool(row.get("has_streaming")),
                has_json_mode=parse_bool(row.get("has_json_mode")),
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )

            if dry_run:
                print(f"  🔍 Would create: {display_name} ({model_id}) -> {provider_name}")
            else:
                session.add(model)
                print(f"  ✅ Created: {display_name} ({model_id}) -> {provider_name}")

            models.append(model)

    return models


def clear_catalog(session: Session, soft_delete: bool = True) -> None:
    """Clear existing catalog data."""
    print("\n🗑️  Clearing existing catalog data...")

    if soft_delete:
        # Soft delete all models
        models = session.exec(
            select(LLMModel).where(LLMModel.is_deleted == False)
        ).all()
        for model in models:
            model.is_deleted = True
            model.deleted_at = datetime.now()
            session.add(model)
        print(f"  Soft-deleted {len(models)} models")

        # Soft delete all providers
        providers = session.exec(
            select(LLMProvider).where(LLMProvider.is_deleted == False)
        ).all()
        for provider in providers:
            provider.is_deleted = True
            provider.deleted_at = datetime.now()
            session.add(provider)
        print(f"  Soft-deleted {len(providers)} providers")
    else:
        # Hard delete (use with caution)
        from sqlmodel import delete
        session.exec(delete(LLMModel))
        session.exec(delete(LLMProvider))
        print("  Hard-deleted all catalog data")


def print_summary(session: Session) -> None:
    """Print catalog summary."""
    providers = session.exec(
        select(LLMProvider).where(LLMProvider.is_deleted == False)
    ).all()

    models = session.exec(
        select(LLMModel).where(LLMModel.is_deleted == False)
    ).all()

    print("\n" + "=" * 60)
    print("📊 CATALOG SUMMARY")
    print("=" * 60)
    print(f"\nProviders: {len(providers)}")
    for p in providers:
        model_count = len([m for m in models if m.provider_id == p.id])
        default_model = next(
            (m for m in models if m.provider_id == p.id and m.is_default),
            None
        )
        default_name = default_model.display_name if default_model else "None"
        print(f"  • {p.name} ({p.provider_type.value}): {model_count} models, default: {default_name}")

    print(f"\nTotal Models: {len(models)}")
    print(f"  • Vision capable: {len([m for m in models if m.has_vision])}")
    print(f"  • Function calling: {len([m for m in models if m.has_function_calling])}")
    print(f"  • Defaults: {len([m for m in models if m.is_default])}")


def main():
    parser = argparse.ArgumentParser(
        description="Load LLM providers and models from CSV files"
    )
    parser.add_argument(
        "--providers",
        type=Path,
        default=Path(__file__).parent / "providers.csv",
        help="Path to providers CSV file"
    )
    parser.add_argument(
        "--models",
        type=Path,
        default=Path(__file__).parent / "models.csv",
        help="Path to models CSV file"
    )
    parser.add_argument(
        "--providers-only",
        action="store_true",
        help="Load only providers"
    )
    parser.add_argument(
        "--models-only",
        action="store_true",
        help="Load only models (providers must exist)"
    )
    parser.add_argument(
        "--clear",
        action="store_true",
        help="Clear existing catalog data before loading"
    )
    parser.add_argument(
        "--hard-delete",
        action="store_true",
        help="Use hard delete instead of soft delete when clearing"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be loaded without making changes"
    )

    args = parser.parse_args()

    print("=" * 60)
    print("🚀 LLM CATALOG LOADER")
    print("=" * 60)

    if args.dry_run:
        print("\n⚠️  DRY RUN MODE - No changes will be made\n")

    with Session(engine) as session:
        try:
            # Clear if requested
            if args.clear and not args.dry_run:
                clear_catalog(session, soft_delete=not args.hard_delete)

            providers = {}

            # Load providers
            if not args.models_only:
                if not args.providers.exists():
                    print(f"❌ Providers file not found: {args.providers}")
                    sys.exit(1)
                providers = load_providers(args.providers, session, args.dry_run)

            # Load models
            if not args.providers_only:
                if not args.models.exists():
                    print(f"❌ Models file not found: {args.models}")
                    sys.exit(1)
                load_models(args.models, session, providers, args.dry_run)

            # Commit changes
            if not args.dry_run:
                session.commit()
                print("\n✅ Changes committed to database")

            # Print summary
            if not args.dry_run:
                print_summary(session)

        except Exception as e:
            session.rollback()
            print(f"\n❌ Error: {e}")
            raise


if __name__ == "__main__":
    main()
