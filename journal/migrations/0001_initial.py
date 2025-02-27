# Generated by Django 3.2.16 on 2023-01-12 01:32

import uuid

import django.core.validators
import django.db.models.deletion
import django.utils.timezone
import markdownx.models
from django.db import migrations, models

import catalog.common.utils
import journal.models.mixins


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("catalog", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Piece",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "uid",
                    models.UUIDField(db_index=True, default=uuid.uuid4, editable=False),
                ),
            ],
            options={
                "abstract": False,
                "base_manager_name": "objects",
            },
            bases=(models.Model, journal.models.mixins.UserOwnedObjectMixin),
        ),
        migrations.CreateModel(
            name="Collection",
            fields=[
                (
                    "piece_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="journal.piece",
                    ),
                ),
                ("visibility", models.PositiveSmallIntegerField(default=0)),
                (
                    "created_time",
                    models.DateTimeField(default=django.utils.timezone.now),
                ),
                (
                    "edited_time",
                    models.DateTimeField(default=django.utils.timezone.now),
                ),
                ("metadata", models.JSONField(default=dict)),
                (
                    "title",
                    models.CharField(default="", max_length=1000, verbose_name="标题"),
                ),
                ("brief", models.TextField(blank=True, default="", verbose_name="简介")),
                (
                    "cover",
                    models.ImageField(
                        blank=True,
                        default="item/default.svg",
                        upload_to=catalog.common.utils.item_cover_path,
                    ),
                ),
                ("collaborative", models.PositiveSmallIntegerField(default=0)),
            ],
            options={
                "abstract": False,
            },
            bases=("journal.piece",),
        ),
        migrations.CreateModel(
            name="CollectionMember",
            fields=[
                (
                    "piece_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="journal.piece",
                    ),
                ),
                ("visibility", models.PositiveSmallIntegerField(default=0)),
                (
                    "created_time",
                    models.DateTimeField(default=django.utils.timezone.now),
                ),
                (
                    "edited_time",
                    models.DateTimeField(default=django.utils.timezone.now),
                ),
                ("metadata", models.JSONField(default=dict)),
                ("position", models.PositiveIntegerField()),
            ],
            options={
                "abstract": False,
            },
            bases=("journal.piece",),
        ),
        migrations.CreateModel(
            name="Comment",
            fields=[
                (
                    "piece_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="journal.piece",
                    ),
                ),
                ("visibility", models.PositiveSmallIntegerField(default=0)),
                (
                    "created_time",
                    models.DateTimeField(default=django.utils.timezone.now),
                ),
                (
                    "edited_time",
                    models.DateTimeField(default=django.utils.timezone.now),
                ),
                ("metadata", models.JSONField(default=dict)),
                ("text", models.TextField()),
            ],
            options={
                "abstract": False,
            },
            bases=("journal.piece",),
        ),
        migrations.CreateModel(
            name="Like",
            fields=[
                (
                    "piece_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="journal.piece",
                    ),
                ),
                ("visibility", models.PositiveSmallIntegerField(default=0)),
                (
                    "created_time",
                    models.DateTimeField(default=django.utils.timezone.now),
                ),
                (
                    "edited_time",
                    models.DateTimeField(default=django.utils.timezone.now),
                ),
            ],
            options={
                "abstract": False,
                "base_manager_name": "objects",
            },
            bases=("journal.piece",),
        ),
        migrations.CreateModel(
            name="Memo",
            fields=[
                (
                    "piece_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="journal.piece",
                    ),
                ),
                ("visibility", models.PositiveSmallIntegerField(default=0)),
                (
                    "created_time",
                    models.DateTimeField(default=django.utils.timezone.now),
                ),
                (
                    "edited_time",
                    models.DateTimeField(default=django.utils.timezone.now),
                ),
                ("metadata", models.JSONField(default=dict)),
            ],
            options={
                "abstract": False,
            },
            bases=("journal.piece",),
        ),
        migrations.CreateModel(
            name="Rating",
            fields=[
                (
                    "piece_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="journal.piece",
                    ),
                ),
                ("visibility", models.PositiveSmallIntegerField(default=0)),
                (
                    "created_time",
                    models.DateTimeField(default=django.utils.timezone.now),
                ),
                (
                    "edited_time",
                    models.DateTimeField(default=django.utils.timezone.now),
                ),
                ("metadata", models.JSONField(default=dict)),
                (
                    "grade",
                    models.PositiveSmallIntegerField(
                        default=0,
                        null=True,
                        validators=[
                            django.core.validators.MaxValueValidator(10),
                            django.core.validators.MinValueValidator(1),
                        ],
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
            bases=("journal.piece",),
        ),
        migrations.CreateModel(
            name="Reply",
            fields=[
                (
                    "piece_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="journal.piece",
                    ),
                ),
                ("title", models.CharField(max_length=500, null=True)),
                ("body", markdownx.models.MarkdownxField()),
            ],
            options={
                "abstract": False,
                "base_manager_name": "objects",
            },
            bases=("journal.piece",),
        ),
        migrations.CreateModel(
            name="Review",
            fields=[
                (
                    "piece_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="journal.piece",
                    ),
                ),
                ("visibility", models.PositiveSmallIntegerField(default=0)),
                (
                    "created_time",
                    models.DateTimeField(default=django.utils.timezone.now),
                ),
                (
                    "edited_time",
                    models.DateTimeField(default=django.utils.timezone.now),
                ),
                ("metadata", models.JSONField(default=dict)),
                ("title", models.CharField(max_length=500)),
                ("body", markdownx.models.MarkdownxField()),
            ],
            options={
                "abstract": False,
            },
            bases=("journal.piece",),
        ),
        migrations.CreateModel(
            name="Shelf",
            fields=[
                (
                    "piece_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="journal.piece",
                    ),
                ),
                ("visibility", models.PositiveSmallIntegerField(default=0)),
                (
                    "created_time",
                    models.DateTimeField(default=django.utils.timezone.now),
                ),
                (
                    "edited_time",
                    models.DateTimeField(default=django.utils.timezone.now),
                ),
                ("metadata", models.JSONField(default=dict)),
                (
                    "shelf_type",
                    models.CharField(
                        choices=[
                            ("wishlist", "未开始"),
                            ("progress", "进行中"),
                            ("complete", "完成"),
                            ("dropped", "放弃"),
                        ],
                        max_length=100,
                    ),
                ),
            ],
            bases=("journal.piece",),
        ),
        migrations.CreateModel(
            name="ShelfMember",
            fields=[
                (
                    "piece_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="journal.piece",
                    ),
                ),
                ("visibility", models.PositiveSmallIntegerField(default=0)),
                (
                    "created_time",
                    models.DateTimeField(default=django.utils.timezone.now),
                ),
                (
                    "edited_time",
                    models.DateTimeField(default=django.utils.timezone.now),
                ),
                ("metadata", models.JSONField(default=dict)),
                ("position", models.PositiveIntegerField()),
            ],
            options={
                "abstract": False,
            },
            bases=("journal.piece",),
        ),
        migrations.CreateModel(
            name="Tag",
            fields=[
                (
                    "piece_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="journal.piece",
                    ),
                ),
                ("visibility", models.PositiveSmallIntegerField(default=0)),
                (
                    "created_time",
                    models.DateTimeField(default=django.utils.timezone.now),
                ),
                (
                    "edited_time",
                    models.DateTimeField(default=django.utils.timezone.now),
                ),
                ("metadata", models.JSONField(default=dict)),
                (
                    "title",
                    models.CharField(
                        max_length=100,
                        validators=[
                            django.core.validators.RegexValidator(
                                inverse_match=True, regex="\\s+"
                            )
                        ],
                    ),
                ),
            ],
            bases=("journal.piece",),
        ),
        migrations.CreateModel(
            name="TagMember",
            fields=[
                (
                    "piece_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="journal.piece",
                    ),
                ),
                ("visibility", models.PositiveSmallIntegerField(default=0)),
                (
                    "created_time",
                    models.DateTimeField(default=django.utils.timezone.now),
                ),
                (
                    "edited_time",
                    models.DateTimeField(default=django.utils.timezone.now),
                ),
                ("metadata", models.JSONField(default=dict)),
                ("position", models.PositiveIntegerField()),
            ],
            options={
                "abstract": False,
            },
            bases=("journal.piece",),
        ),
        migrations.CreateModel(
            name="ShelfLogEntry",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "shelf_type",
                    models.CharField(
                        choices=[
                            ("wishlist", "未开始"),
                            ("progress", "进行中"),
                            ("complete", "完成"),
                            ("dropped", "放弃"),
                        ],
                        max_length=100,
                        null=True,
                    ),
                ),
                ("timestamp", models.DateTimeField(default=django.utils.timezone.now)),
                ("metadata", models.JSONField(default=dict)),
                ("created_time", models.DateTimeField(auto_now_add=True)),
                ("edited_time", models.DateTimeField(auto_now=True)),
                (
                    "item",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT, to="catalog.item"
                    ),
                ),
            ],
        ),
    ]
