using Microsoft.AspNetCore.SignalR;

namespace Duohabbit.Hubs.Hubs;

public class HabitHub : Hub
{
    public async Task JoinHabitGroup(string habitId)
    {
        await Groups.AddToGroupAsync(Context.ConnectionId, $"habit-{habitId}");
    }

    public async Task LeaveHabitGroup(string habitId)
    {
        await Groups.RemoveFromGroupAsync(Context.ConnectionId, $"habit-{habitId}");
    }

    public async Task NotifyCompletion(string habitId, Guid userId)
    {
        await Clients.Group($"habit-{habitId}").SendAsync("ParticipantCompleted", userId);
    }

    public async Task NotifyUndo(string habitId, Guid userId)
    {
        await Clients.Group($"habit-{habitId}").SendAsync("ParticipantUndid", userId);
    }
}