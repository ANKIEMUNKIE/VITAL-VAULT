"""Initial schema — all tables, indexes, constraints, and seed data.

Revision ID: 001_initial_schema
Revises: None
Create Date: 2026-04-16
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision: str = "001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- Enable pgcrypto extension ---
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")

    # --- users ---
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("email", sa.Text(), nullable=False),
        sa.Column("phone_number", sa.Text(), nullable=True),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("is_email_verified", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("mfa_secret", sa.Text(), nullable=True),
        sa.Column("mfa_enabled", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("failed_login_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("idx_users_email", "users", ["email"], unique=True)
    op.create_index("idx_users_role", "users", ["role"])

    # --- refresh_tokens ---
    op.create_table(
        "refresh_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token_hash", sa.Text(), nullable=False, unique=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_revoked", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("idx_refresh_tokens_user_id", "refresh_tokens", ["user_id"])

    # --- clinics ---
    op.create_table(
        "clinics",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("license_number", sa.Text(), nullable=False, unique=True),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("contact_email", sa.Text(), nullable=False),
        sa.Column("api_key_hash", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

    # --- clinic_memberships ---
    op.create_table(
        "clinic_memberships",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("clinic_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("clinics.id"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("role", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("clinic_id", "user_id", name="uq_clinic_user"),
    )

    # --- patient_profiles ---
    op.create_table(
        "patient_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("full_name", sa.LargeBinary(), nullable=False),
        sa.Column("date_of_birth", sa.LargeBinary(), nullable=False),
        sa.Column("gender", sa.Text(), nullable=True),
        sa.Column("blood_group", sa.Text(), nullable=True),
        sa.Column("allergies", sa.LargeBinary(), nullable=True),
        sa.Column("emergency_contact", sa.LargeBinary(), nullable=True),
        sa.Column("storage_used_bytes", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("storage_quota_bytes", sa.BigInteger(), nullable=False, server_default="524288000"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("idx_patient_profiles_user_id", "patient_profiles", ["user_id"])

    # --- doctor_profiles ---
    op.create_table(
        "doctor_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("full_name", sa.Text(), nullable=False),
        sa.Column("license_number", sa.Text(), nullable=False, unique=True),
        sa.Column("specialization", sa.Text(), nullable=False),
        sa.Column("clinic_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("clinics.id"), nullable=True),
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("idx_doctor_profiles_clinic_id", "doctor_profiles", ["clinic_id"])

    # --- document_categories ---
    op.create_table(
        "document_categories",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("slug", sa.Text(), nullable=False, unique=True),
        sa.Column("label", sa.Text(), nullable=False),
        sa.Column("icon_key", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

    # --- medical_records ---
    op.create_table(
        "medical_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("patient_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("patient_profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("category_id", sa.Integer(), sa.ForeignKey("document_categories.id"), nullable=True),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("document_date", sa.Date(), nullable=True),
        sa.Column("storage_key", sa.Text(), nullable=False),
        sa.Column("storage_bucket", sa.Text(), nullable=False),
        sa.Column("file_name_original", sa.Text(), nullable=False),
        sa.Column("file_size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("mime_type", sa.Text(), nullable=False),
        sa.Column("checksum_sha256", sa.Text(), nullable=False),
        sa.Column("processing_status", sa.Text(), nullable=False, server_default="PENDING"),
        sa.Column("processing_error", sa.Text(), nullable=True),
        sa.Column("ocr_raw_text", sa.LargeBinary(), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("shared_with_doctor", postgresql.ARRAY(postgresql.UUID(as_uuid=True)), server_default="{}"),
        sa.Column("tags", postgresql.ARRAY(sa.Text()), server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("idx_medical_records_patient_id", "medical_records", ["patient_id"])
    op.create_index("idx_medical_records_category_id", "medical_records", ["category_id"])
    op.create_index("idx_medical_records_document_date", "medical_records", [sa.text("document_date DESC")])
    op.create_index("idx_medical_records_processing_status", "medical_records", ["processing_status"])
    op.create_index("idx_medical_records_tags", "medical_records", ["tags"], postgresql_using="gin")

    # --- record_extractions ---
    op.create_table(
        "record_extractions",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("record_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("medical_records.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("diagnosed_conditions", sa.LargeBinary(), nullable=True),
        sa.Column("extracted_medications", sa.LargeBinary(), nullable=True),
        sa.Column("extracted_dates", postgresql.JSONB(), nullable=True),
        sa.Column("doctor_name", sa.LargeBinary(), nullable=True),
        sa.Column("hospital_name", sa.LargeBinary(), nullable=True),
        sa.Column("ai_summary", sa.LargeBinary(), nullable=True),
        sa.Column("confidence_score", sa.Numeric(4, 3), nullable=True),
        sa.Column("extraction_model", sa.Text(), nullable=True),
        sa.Column("extraction_version", sa.Text(), nullable=True),
        sa.Column("manually_corrected", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("manual_corrections", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("idx_record_extractions_record_id", "record_extractions", ["record_id"])

    # --- medications ---
    op.create_table(
        "medications",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("patient_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("patient_profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source_record_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("medical_records.id"), nullable=True),
        sa.Column("name", sa.LargeBinary(), nullable=False),
        sa.Column("generic_name", sa.LargeBinary(), nullable=True),
        sa.Column("dosage", sa.Text(), nullable=True),
        sa.Column("frequency", sa.Text(), nullable=True),
        sa.Column("route", sa.Text(), nullable=True),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("prescribed_by", sa.Text(), nullable=True),
        sa.Column("notes", sa.LargeBinary(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("idx_medications_patient_id", "medications", ["patient_id"])
    op.create_index("idx_medications_end_date", "medications", ["end_date"])

    # --- reminders ---
    op.create_table(
        "reminders",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("patient_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("patient_profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("medication_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("medications.id"), nullable=True),
        sa.Column("record_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("medical_records.id"), nullable=True),
        sa.Column("reminder_type", sa.Text(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("body", sa.Text(), nullable=True),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("recurrence_rule", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("delivery_channels", postgresql.ARRAY(sa.Text()), nullable=False, server_default="{PUSH}"),
        sa.Column("last_sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("next_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("idx_reminders_patient_id", "reminders", ["patient_id"])
    op.create_index("idx_reminders_type", "reminders", ["reminder_type"])

    # --- appointments ---
    op.create_table(
        "appointments",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("patient_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("patient_profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("doctor_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("doctor_profiles.id"), nullable=True),
        sa.Column("source_record_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("medical_records.id"), nullable=True),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("location", sa.Text(), nullable=True),
        sa.Column("appointment_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("notes", sa.LargeBinary(), nullable=True),
        sa.Column("status", sa.Text(), nullable=False, server_default="SCHEDULED"),
        sa.Column("reminder_sent", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("idx_appointments_patient_id", "appointments", ["patient_id"])
    op.create_index("idx_appointments_doctor_id", "appointments", ["doctor_id"])

    # --- subscription_tiers ---
    op.create_table(
        "subscription_tiers",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("slug", sa.Text(), nullable=False, unique=True),
        sa.Column("label", sa.Text(), nullable=False),
        sa.Column("storage_quota_bytes", sa.BigInteger(), nullable=False),
        sa.Column("max_reminders", sa.Integer(), nullable=True),
        sa.Column("ai_summaries_enabled", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("price_monthly_cents", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

    # --- subscriptions ---
    op.create_table(
        "subscriptions",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("tier_id", sa.Integer(), sa.ForeignKey("subscription_tiers.id"), nullable=False),
        sa.Column("status", sa.Text(), nullable=False, server_default="ACTIVE"),
        sa.Column("current_period_end", sa.Date(), nullable=True),
        sa.Column("stripe_customer_id", sa.Text(), nullable=True),
        sa.Column("stripe_sub_id", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("idx_subscriptions_user_id", "subscriptions", ["user_id"])

    # --- audit_logs ---
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("actor_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("target_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("action", sa.Text(), nullable=False),
        sa.Column("resource_type", sa.Text(), nullable=False),
        sa.Column("resource_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("ip_address", postgresql.INET(), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("request_id", sa.Text(), nullable=True),
        sa.Column("metadata", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("idx_audit_logs_actor", "audit_logs", ["actor_user_id", sa.text("created_at DESC")])
    op.create_index("idx_audit_logs_target", "audit_logs", ["target_user_id", sa.text("created_at DESC")])
    op.create_index("idx_audit_logs_action", "audit_logs", ["action"])

    # --- Seed data: document_categories ---
    op.execute("""
        INSERT INTO document_categories (slug, label) VALUES
        ('lab_report',    'Lab Report'),
        ('prescription',  'Prescription'),
        ('imaging',       'Medical Imaging (X-Ray / MRI / CT)'),
        ('discharge',     'Discharge Summary'),
        ('vaccination',   'Vaccination Record'),
        ('insurance',     'Insurance Document'),
        ('other',         'Other')
    """)

    # --- Seed data: subscription_tiers ---
    op.execute("""
        INSERT INTO subscription_tiers (slug, label, storage_quota_bytes, max_reminders, ai_summaries_enabled, price_monthly_cents) VALUES
        ('free', 'Free',           524288000,   5,    false, 0),
        ('pro',  'Pro',            0,           NULL, true,  999),
        ('b2b',  'Business (B2B)', 0,           NULL, true,  4999)
    """)

    # --- Updated_at trigger function ---
    op.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql
    """)

    # Apply the trigger to all tables with updated_at
    for table in [
        "users", "refresh_tokens", "patient_profiles", "doctor_profiles",
        "document_categories", "medical_records", "record_extractions",
        "medications", "reminders", "appointments", "subscription_tiers",
        "subscriptions", "clinics",
    ]:
        op.execute(f"""
            CREATE TRIGGER trigger_update_{table}_updated_at
            BEFORE UPDATE ON {table}
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()
        """)


def downgrade() -> None:
    # Drop triggers
    for table in [
        "users", "refresh_tokens", "patient_profiles", "doctor_profiles",
        "document_categories", "medical_records", "record_extractions",
        "medications", "reminders", "appointments", "subscription_tiers",
        "subscriptions", "clinics",
    ]:
        op.execute(f"DROP TRIGGER IF EXISTS trigger_update_{table}_updated_at ON {table}")
    op.execute("DROP FUNCTION IF EXISTS update_updated_at_column()")

    # Drop tables in reverse dependency order
    op.drop_table("audit_logs")
    op.drop_table("subscriptions")
    op.drop_table("subscription_tiers")
    op.drop_table("appointments")
    op.drop_table("reminders")
    op.drop_table("medications")
    op.drop_table("record_extractions")
    op.drop_table("medical_records")
    op.drop_table("document_categories")
    op.drop_table("doctor_profiles")
    op.drop_table("patient_profiles")
    op.drop_table("clinic_memberships")
    op.drop_table("clinics")
    op.drop_table("refresh_tokens")
    op.drop_table("users")
