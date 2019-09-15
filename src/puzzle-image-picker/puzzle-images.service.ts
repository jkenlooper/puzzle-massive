import FetchService from "../site/fetch.service";

export interface PuzzleImageData {
  src: string;
  puzzle_id: string;
  status: number;
  pieces: number;
  redo_date?: string;
  is_active: number;
  is_new: number;
  is_recent: number;
  is_original: number;
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

export interface PuzzleListResponse {
  puzzles: Array<PuzzleImageData>;
  totalPuzzleCount: number;
  puzzleCount: number;
  pageSize: number;
  currentPage: number;
  maxPieces: number;
}

export enum Status {
  ACTIVE = 1,
  IN_QUEUE = 2,
  COMPLETED = 3,
  FROZEN = 4,
}
export const PuzzleAvailableStatuses = [
  Status.ACTIVE,
  Status.IN_QUEUE,
  Status.COMPLETED,
];

class PuzzleImagesService {
  constructor() {}

  getPlayerPuzzleImages(): Promise<PlayerPuzzleListResponse> {
    const playerPuzzleImagesService = new FetchService(
      "/newapi/player-puzzle-list/"
    );

    const puzzleList: Promise<
      PlayerPuzzleListResponse
    > = playerPuzzleImagesService
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
      case Status.IN_QUEUE:
        return has_m_date ? "" : "New";
        break;
      case Status.COMPLETED:
        return "Completed";
        break;
      case Status.FROZEN:
        return "Frozen";
        break;
      default:
        return "Unavailable";
        break;
    }
  }
}

export const puzzleImagesService = new PuzzleImagesService();
