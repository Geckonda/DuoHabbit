using Duohabbit.Core.Entities;

namespace Duohabbit.Core.Interfaces;

public interface ICompletionRepository
{
    Task<Completion?> GetParticipantCompletionAsync(Guid participantId, string periodKey);
    Task<Completion> AddCompletionAsync(Completion completion);
    Task UndoCompletionAsync(Guid completionId);
    Task<bool> HasParticipantCompletedAsync(Guid participantId, string periodKey);
}