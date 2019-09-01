import FetchService from "../site/fetch.service";
import { getTimePassed } from "../site/utilities";

interface PuzzleImageData {
  src: string;
  puzzle_id: string;
  status: number;
  pieces: number;
  redo_date: string;
  is_recent: number;
  is_original: number;
  seconds_from_now: number;
  owner: number;
  title: string;
  author_link: string;
  author_name: string;
  source: string;
  license_source: string;
  license_name: string;
  license_title: string;
}

interface PuzzleImage {
  src: string;
  puzzleId: string;
  pieces: number;
  isActive: boolean;
  isRecent: boolean;
  isComplete: boolean;
  isAvailable: boolean;
  isNew: boolean;
  isFrozen: boolean;
  isOriginal: boolean;
  statusText: string;
  timeSince: string;
  secondsFromNow: null | number;
  owner: number;
  title: string;
  authorLink: string;
  authorName: string;
  source: string;
  licenseSource: string;
  licenseName: string;
  licenseTitle: string;
}

type PuzzleImagesData = Array<PuzzleImageData>;
export type PuzzleImages = Array<PuzzleImage>;

enum Status {
  ACTIVE = 1,
  IN_QUEUE = 2,
  COMPLETED = 3,
  FROZEN = 4,
}
const PuzzleAvailableStatuses = [
  Status.ACTIVE,
  Status.IN_QUEUE,
  Status.COMPLETED,
];

class PuzzleImagesService {
  private puzzleImages: undefined | Promise<PuzzleImages>;

  constructor() {}

  getPuzzleImages(): Promise<PuzzleImages> {
    if (this.puzzleImages) {
      return this.puzzleImages;
    } else {
      const puzzleImagesService = new FetchService(
        `/chill/site/api/puzzle-images/`
      );

      this.puzzleImages = puzzleImagesService
        .get<PuzzleImagesData>()
        .then((puzzleImagesData) => {
          return puzzleImagesData.map((puzzle) => {
            return {
              src: puzzle.src,
              puzzleId: puzzle.puzzle_id,
              pieces: puzzle.pieces,
              isActive:
                !puzzle.is_recent &&
                puzzle.status != Status.COMPLETED &&
                PuzzleAvailableStatuses.includes(puzzle.status) &&
                puzzle.seconds_from_now !== null,
              isRecent: !!puzzle.is_recent,
              isComplete: puzzle.status === Status.COMPLETED,
              isAvailable: PuzzleAvailableStatuses.includes(puzzle.status),
              isNew:
                [Status.ACTIVE, Status.IN_QUEUE].includes(puzzle.status) &&
                puzzle.seconds_from_now === null,
              isFrozen: puzzle.status == Status.FROZEN,
              isOriginal: !!puzzle.is_original,
              statusText: this.statusToStatusText(
                puzzle.status,
                !!puzzle.is_recent,
                puzzle.seconds_from_now != null
              ),
              timeSince:
                puzzle.seconds_from_now != null
                  ? getTimePassed(puzzle.seconds_from_now)
                  : "",
              secondsFromNow: puzzle.seconds_from_now,
              owner: puzzle.owner,
              title: puzzle.title,
              authorLink: puzzle.author_link,
              authorName: puzzle.author_name,
              source: puzzle.source,
              licenseSource: puzzle.license_source,
              licenseName: puzzle.license_name,
              licenseTitle: puzzle.license_title,
            };
          });
        });
      return this.puzzleImages;
    }
  }

  private statusToStatusText(
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
