using System;
using Microsoft.EntityFrameworkCore.Migrations;

#nullable disable

namespace Duohabbit.Infrastructure.Migrations
{
    /// <inheritdoc />
    public partial class init : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.CreateTable(
                name: "Habits",
                columns: table => new
                {
                    Id = table.Column<Guid>(type: "uuid", nullable: false),
                    Title = table.Column<string>(type: "character varying(200)", maxLength: 200, nullable: false),
                    Description = table.Column<string>(type: "character varying(1000)", maxLength: 1000, nullable: false),
                    OwnerId = table.Column<Guid>(type: "uuid", nullable: false),
                    Schedule = table.Column<string>(type: "text", nullable: false),
                    Deadline = table.Column<TimeSpan>(type: "interval", nullable: false),
                    CreatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    IsActive = table.Column<bool>(type: "boolean", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_Habits", x => x.Id);
                });

            migrationBuilder.CreateTable(
                name: "HabitParticipants",
                columns: table => new
                {
                    Id = table.Column<Guid>(type: "uuid", nullable: false),
                    HabitId = table.Column<Guid>(type: "uuid", nullable: false),
                    UserId = table.Column<Guid>(type: "uuid", nullable: false),
                    JoinedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    IsActive = table.Column<bool>(type: "boolean", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_HabitParticipants", x => x.Id);
                    table.ForeignKey(
                        name: "FK_HabitParticipants_Habits_HabitId",
                        column: x => x.HabitId,
                        principalTable: "Habits",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateTable(
                name: "HabitPeriods",
                columns: table => new
                {
                    Id = table.Column<Guid>(type: "uuid", nullable: false),
                    HabitId = table.Column<Guid>(type: "uuid", nullable: false),
                    PeriodKey = table.Column<string>(type: "text", nullable: false),
                    Status = table.Column<int>(type: "integer", nullable: false),
                    CalculatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_HabitPeriods", x => x.Id);
                    table.ForeignKey(
                        name: "FK_HabitPeriods_Habits_HabitId",
                        column: x => x.HabitId,
                        principalTable: "Habits",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateTable(
                name: "Completions",
                columns: table => new
                {
                    Id = table.Column<Guid>(type: "uuid", nullable: false),
                    HabitParticipantId = table.Column<Guid>(type: "uuid", nullable: false),
                    PeriodKey = table.Column<string>(type: "text", nullable: false),
                    CompletedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    IsUndone = table.Column<bool>(type: "boolean", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_Completions", x => x.Id);
                    table.ForeignKey(
                        name: "FK_Completions_HabitParticipants_HabitParticipantId",
                        column: x => x.HabitParticipantId,
                        principalTable: "HabitParticipants",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateIndex(
                name: "IX_Completions_HabitParticipantId_PeriodKey",
                table: "Completions",
                columns: new[] { "HabitParticipantId", "PeriodKey" },
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_HabitParticipants_HabitId_UserId",
                table: "HabitParticipants",
                columns: new[] { "HabitId", "UserId" },
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_HabitPeriods_HabitId_PeriodKey",
                table: "HabitPeriods",
                columns: new[] { "HabitId", "PeriodKey" },
                unique: true);
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropTable(
                name: "Completions");

            migrationBuilder.DropTable(
                name: "HabitPeriods");

            migrationBuilder.DropTable(
                name: "HabitParticipants");

            migrationBuilder.DropTable(
                name: "Habits");
        }
    }
}
