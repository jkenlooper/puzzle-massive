import FetchService from "./fetch.service";
// Should match api/api/constants.py
export var Status;
(function (Status) {
  Status[Status["ACTIVE"] = 1] = "ACTIVE";
  Status[Status["IN_QUEUE"] = 2] = "IN_QUEUE";
  Status[Status["COMPLETED"] = 3] = "COMPLETED";
  Status[Status["FROZEN"] = 4] = "FROZEN";
  Status[Status["BUGGY_UNLISTED"] = 5] = "BUGGY_UNLISTED";
  Status[Status["DELETED_REQUEST"] = -13] = "DELETED_REQUEST";
  Status[Status["MAINTENANCE"] = -30] = "MAINTENANCE";
  Status[Status["NEEDS_MODERATION"] = 0] = "NEEDS_MODERATION";
  Status[Status["FAILED_LICENSE"] = -1] = "FAILED_LICENSE";
  Status[Status["NO_ATTRIBUTION"] = -2] = "NO_ATTRIBUTION";
  Status[Status["REBUILD"] = -3] = "REBUILD";
  Status[Status["IN_RENDER_QUEUE"] = -5] = "IN_RENDER_QUEUE";
  Status[Status["RENDERING"] = -6] = "RENDERING";
  Status[Status["RENDERING_FAILED"] = -7] = "RENDERING_FAILED";
  Status[Status["DELETED_LICENSE"] = -10] = "DELETED_LICENSE";
  Status[Status["DELETED_INAPT"] = -11] = "DELETED_INAPT";
  Status[Status["DELETED_OLD"] = -12] = "DELETED_OLD";
  Status[Status["SUGGESTED"] = -20] = "SUGGESTED";
  Status[Status["SUGGESTED_DONE"] = -21] = "SUGGESTED_DONE";
})(Status || (Status = {}));
export const PuzzleAvailableStatuses = [
  Status.ACTIVE,
  Status.IN_QUEUE,
  Status.COMPLETED,
  Status.BUGGY_UNLISTED,
];
class PuzzleImagesService {
  constructor() {}
  getPlayerPuzzleImages() {
    const playerPuzzleImagesService = new FetchService(
      "/newapi/player-puzzle-list/",
    );
    const puzzleList = playerPuzzleImagesService
      .get()
      .then((playerPuzzleListResponse) => {
        return {
          puzzles: playerPuzzleListResponse.puzzles,
        };
      });
    return puzzleList;
  }
  getGalleryPuzzleImages() {
    const puzzleImagesService = new FetchService(
      `/newapi/gallery-puzzle-list/`,
    );
    const puzzleList = puzzleImagesService.get().then((puzzleListResponse) => {
      return {
        puzzles: puzzleListResponse.puzzles,
      };
    });
    return puzzleList;
  }
  statusToStatusText(status, is_recent, has_m_date) {
    if (is_recent && status !== Status.FROZEN) {
      return "Recent";
    }
    switch (status) {
      case Status.ACTIVE:
        return has_m_date ? "" : "New";
        break;
      case Status.COMPLETED:
        return "Completed";
        break;
      case Status.IN_QUEUE:
        return "In Queue";
        break;
      case Status.FROZEN:
        return "Frozen";
        break;
      case Status.BUGGY_UNLISTED:
        return "Buggy";
        break;
      case Status.NEEDS_MODERATION:
        return "Needs Moderation";
        break;
      case Status.FAILED_LICENSE:
        return "Failed License";
        break;
      case Status.NO_ATTRIBUTION:
        return "No Attribution";
        break;
      case Status.REBUILD:
        return "Rebuild";
        break;
      case Status.IN_RENDER_QUEUE:
        return "In Render Queue";
        break;
      case Status.RENDERING:
        return "Rendering";
        break;
      case Status.RENDERING_FAILED:
        return "Rendering Failed";
        break;
      case Status.DELETED_LICENSE:
        return "Deleted License";
        break;
      case Status.DELETED_INAPT:
        return "Deleted Inappropriate";
        break;
      case Status.DELETED_OLD:
        return "Deleted Old";
        break;
      case Status.DELETED_REQUEST:
        return "Deleted Request";
        break;
      case Status.SUGGESTED:
        return "Suggested";
        break;
      case Status.SUGGESTED_DONE:
        return "Suggested Done";
        break;
      case Status.MAINTENANCE:
        return "Maintenance";
        break;
      default:
        return "Unavailable";
        break;
    }
  }
}
export const puzzleImagesService = new PuzzleImagesService();
