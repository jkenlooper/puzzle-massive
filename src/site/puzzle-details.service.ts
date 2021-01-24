import FetchService from "./fetch.service";

export interface PuzzleInstanceDetails {
  deletePenalty: number;
  canFreeze: boolean;
  canDelete: boolean;
  canReset: boolean;
  hasActions: boolean;
  deleteDisabledMessage: string; //Not enough dots to delete this puzzle
  isFrozen: boolean;
  status: number;
}

export interface PuzzleOriginalDetails {
  highestBid: number;
  canBump: boolean;
  hasActions: boolean;
  bumpDisabledMessage: string; //Not enough dots to delete this puzzle
  status: number;
}

class PuzzleDetailsService {
  private _puzzleOriginalDetailsCache:
    | Promise<PuzzleOriginalDetails>
    | undefined;

  constructor() {}

  getPuzzleInstanceDetails(puzzleId: string): Promise<PuzzleInstanceDetails> {
    const puzzleDetailsService = new FetchService(
      `/newapi/puzzle-instance-details/${puzzleId}/`
    );

    return puzzleDetailsService
      .get<PuzzleInstanceDetails>()
      .then((puzzleDetails) => {
        return puzzleDetails;
      });
  }

  patchPuzzleInstanceDetails(
    puzzleId: string,
    action: string
  ): Promise<PuzzleInstanceDetails> {
    const puzzleDetailsService = new FetchService(
      `/newapi/puzzle-instance-details/${puzzleId}/`
    );

    const data = {
      action: action,
    };
    return puzzleDetailsService
      .patch<PuzzleInstanceDetails>(data)
      .then((puzzleDetails) => {
        return puzzleDetails;
      });
  }

  getPuzzleOriginalDetails(puzzleId: string): Promise<PuzzleOriginalDetails> {
    if (this._puzzleOriginalDetailsCache) {
      return Promise.resolve(this._puzzleOriginalDetailsCache);
    }
    const puzzleDetailsService = new FetchService(
      `/newapi/puzzle-original-details/${puzzleId}/`
    );

    this._puzzleOriginalDetailsCache = puzzleDetailsService
      .get<PuzzleOriginalDetails>()
      .then((puzzleDetails) => {
        return puzzleDetails;
      })
      .finally(() => {
        window.setTimeout(() => {
          // Invalidate the cache
          this._puzzleOriginalDetailsCache = undefined;
        }, 1000);
      });
    return this._puzzleOriginalDetailsCache;
  }

  patchPuzzleOriginalDetails(
    puzzleId: string,
    action: string
  ): Promise<PuzzleOriginalDetails> {
    const puzzleDetailsService = new FetchService(
      `/newapi/puzzle-original-details/${puzzleId}/`
    );

    const data = {
      action: action,
    };
    return puzzleDetailsService
      .patch<PuzzleOriginalDetails>(data)
      .then((puzzleDetails) => {
        return puzzleDetails;
      });
  }
}

export const puzzleDetailsService = new PuzzleDetailsService();
