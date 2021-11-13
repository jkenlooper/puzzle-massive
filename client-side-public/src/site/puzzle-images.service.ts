import FetchService from "./fetch.service";

export interface PuzzleImageData {
  src: string;
  puzzle_id: string;
  status: number;
  pieces: number;
  permission: number;
  queue: number;
  redo_date?: string;
  is_active: number;
  is_new: number;
  is_recent: number;
  is_original: number;
  is_in_puzzle_instance_slot: number;
  seconds_from_now: number | null;
  owner: number;
  title: string;
  author_link: string;
  author_name: string;
  source: string;
  license_source: string;
  license_name: string;
  license_title: string;
}

export interface PlayerPuzzleListResponse {
  puzzles: Array<PuzzleImageData>;
}
export interface GalleryPuzzleListResponse {
  puzzles: Array<PuzzleImageData>;
}

export interface PuzzleListResponse {
  puzzles: Array<PuzzleImageData>;
  totalPuzzleCount: number;
  puzzleCount: number;
  pageSize: number;
  currentPage: number;
  maxPieces: number;
}

// Should match api/api/constants.py
export enum Status {
  ACTIVE = 1,
  IN_QUEUE = 2,
  COMPLETED = 3,
  FROZEN = 4,
  BUGGY_UNLISTED = 5,
  DELETED_REQUEST = -13,
  MAINTENANCE = -30,
  NEEDS_MODERATION = 0,
  FAILED_LICENSE = -1,
  NO_ATTRIBUTION = -2,
  REBUILD = -3,
  IN_RENDER_QUEUE = -5,
  RENDERING = -6,
  RENDERING_FAILED = -7,
  DELETED_LICENSE = -10,
  DELETED_INAPT = -11,
  DELETED_OLD = -12,
  SUGGESTED = -20,
  SUGGESTED_DONE = -21,
}
export const PuzzleAvailableStatuses = [
  Status.ACTIVE,
  Status.IN_QUEUE,
  Status.COMPLETED,
  Status.BUGGY_UNLISTED,
];

class PuzzleImagesService {
  constructor() {}

  getPlayerPuzzleImages(): Promise<PlayerPuzzleListResponse> {
    const playerPuzzleImagesService = new FetchService(
      "/newapi/player-puzzle-list/"
    );

    const puzzleList: Promise<PlayerPuzzleListResponse> = playerPuzzleImagesService
      .get<PlayerPuzzleListResponse>()
      .then((playerPuzzleListResponse) => {
        return {
          puzzles: playerPuzzleListResponse.puzzles,
        };
      });
    return puzzleList;
  }

  getPuzzleImages(
    status: Array<string>,
    _type: Array<string>,
    piecesMin: number,
    piecesMax: number,
    page: number,
    orderby: string
  ): Promise<PuzzleListResponse> {
    const query = new window.URLSearchParams();
    status.forEach((statusName) => {
      query.append("status", statusName);
    });

    query.append("pieces_min", piecesMin.toString());
    query.append("pieces_max", piecesMax.toString());
    query.append("page", page.toString());

    _type.forEach((typeName) => {
      query.append("type", typeName);
    });

    query.append("orderby", orderby);

    const puzzleImagesService = new FetchService(
      `/newapi/puzzle-list/?${query.toString()}`
    );

    const puzzleList: Promise<PuzzleListResponse> = puzzleImagesService
      .get<PuzzleListResponse>()
      .then((puzzleListResponse) => {
        return {
          puzzles: puzzleListResponse.puzzles,
          totalPuzzleCount: puzzleListResponse.totalPuzzleCount,
          puzzleCount: puzzleListResponse.puzzleCount,
          pageSize: puzzleListResponse.pageSize,
          currentPage: puzzleListResponse.currentPage,
          maxPieces: puzzleListResponse.maxPieces,
        };
      });
    return puzzleList;
  }

  getGalleryPuzzleImages(): Promise<GalleryPuzzleListResponse> {
    const puzzleImagesService = new FetchService(
      `/newapi/gallery-puzzle-list/`
    );

    const puzzleList: Promise<GalleryPuzzleListResponse> = puzzleImagesService
      .get<GalleryPuzzleListResponse>()
      .then((puzzleListResponse) => {
        return {
          puzzles: puzzleListResponse.puzzles,
        };
      });
    return puzzleList;
  }

  public statusToStatusText(
    status: number,
    is_recent: boolean,
    has_m_date: boolean
  ): string {
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
