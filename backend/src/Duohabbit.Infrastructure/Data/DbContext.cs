using Duohabbit.Core.Entities;
using Microsoft.EntityFrameworkCore;
using System.Collections.Generic;
using System.Reflection.Emit;

namespace Duohabbit.Infrastructure.Data;

public class ApplicationDbContext : DbContext
{
    public ApplicationDbContext(DbContextOptions<ApplicationDbContext> options)
        : base(options)
    {
    }

    public DbSet<Habit> Habits { get; set; }
    public DbSet<HabitParticipant> HabitParticipants { get; set; }
    public DbSet<HabitPeriod> HabitPeriods { get; set; }
    public DbSet<Completion> Completions { get; set; }

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        base.OnModelCreating(modelBuilder);

        // Habit configuration
        modelBuilder.Entity<Habit>(entity =>
        {
            entity.HasKey(e => e.Id);
            entity.Property(e => e.Title).IsRequired().HasMaxLength(200);
            entity.Property(e => e.Description).HasMaxLength(1000);
            entity.Property(e => e.Schedule).IsRequired();

            entity.HasMany(e => e.Participants)
                .WithOne(e => e.Habit)
                .HasForeignKey(e => e.HabitId)
                .OnDelete(DeleteBehavior.Cascade);

            entity.HasMany(e => e.Periods)
                .WithOne(e => e.Habit)
                .HasForeignKey(e => e.HabitId)
                .OnDelete(DeleteBehavior.Cascade);
        });

        // HabitParticipant configuration
        modelBuilder.Entity<HabitParticipant>(entity =>
        {
            entity.HasKey(e => e.Id);
            entity.HasIndex(e => new { e.HabitId, e.UserId }).IsUnique();

            entity.HasMany(e => e.Completions)
                .WithOne(e => e.Participant)
                .HasForeignKey(e => e.HabitParticipantId)
                .OnDelete(DeleteBehavior.Cascade);
        });

        // Completion configuration
        modelBuilder.Entity<Completion>(entity =>
        {
            entity.HasKey(e => e.Id);
            entity.HasIndex(e => new { e.HabitParticipantId, e.PeriodKey }).IsUnique();
        });

        // HabitPeriod configuration
        modelBuilder.Entity<HabitPeriod>(entity =>
        {
            entity.HasKey(e => e.Id);
            entity.HasIndex(e => new { e.HabitId, e.PeriodKey }).IsUnique();
        });

        
    }
}