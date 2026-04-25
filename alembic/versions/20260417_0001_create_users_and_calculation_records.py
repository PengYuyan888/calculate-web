"""创建 users 表和 calculation_records 表。"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260417_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column(
            "id",
            sa.Integer(),
            autoincrement=True,
            nullable=False,
            comment="用户主键ID",
        ),
        sa.Column(
            "username",
            sa.String(length=50),
            nullable=False,
            comment="用户名",
        ),
        sa.Column(
            "email",
            sa.String(length=100),
            nullable=False,
            comment="用户邮箱",
        ),
        sa.Column(
            "hashed_password",
            sa.String(length=200),
            nullable=False,
            comment="密码哈希值",
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            comment="账户是否启用",
        ),
        sa.Column(
            "is_verified",
            sa.Boolean(),
            nullable=False,
            comment="邮箱是否已验证",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            comment="创建时间（UTC）",
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            comment="更新时间（UTC）",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
        sa.UniqueConstraint("username"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=False)
    op.create_index(op.f("ix_users_username"), "users", ["username"], unique=False)

    op.create_table(
        "calculation_records",
        sa.Column(
            "id",
            sa.Integer(),
            autoincrement=True,
            nullable=False,
            comment="计算记录主键ID",
        ),
        sa.Column(
            "user_id",
            sa.Integer(),
            nullable=False,
            comment="所属用户ID",
        ),
        sa.Column(
            "project_name",
            sa.String(length=200),
            nullable=True,
            comment="项目名称，匿名计算时可为空",
        ),
        sa.Column(
            "scaffold_type",
            sa.String(length=50),
            nullable=False,
            comment="脚手架类型",
        ),
        sa.Column(
            "status",
            sa.String(length=20),
            nullable=False,
            comment="计算状态（passed或failed）",
        ),
        sa.Column(
            "overall_passed",
            sa.Boolean(),
            nullable=False,
            comment="整体验算是否通过",
        ),
        sa.Column(
            "request_snapshot",
            sa.Text(),
            nullable=True,
            comment="请求参数快照JSON字符串",
        ),
        sa.Column(
            "result_snapshot",
            sa.Text(),
            nullable=True,
            comment="结果摘要快照JSON字符串",
        ),
        sa.Column(
            "report_path",
            sa.String(length=500),
            nullable=True,
            comment="Word计算书相对路径",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            comment="创建时间（UTC）",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_calculation_records_user_id"),
        "calculation_records",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_calculation_records_user_id"),
        table_name="calculation_records",
    )
    op.drop_table("calculation_records")
    op.drop_index(op.f("ix_users_username"), table_name="users")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")
