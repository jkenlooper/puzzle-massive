import FetchService from "./fetch.service";

export interface PuzzleDetails {
  deletePenalty: number;
  canDelete: boolean;
  deleteDisabledMessage: string; //Not enough dots to delete this puzzle
  isFrozen: boolean;
  status: number;
}

class PuzzleDetailsService {
  constructor() {}

  getPuzzleDetails(puzzleId: string): Promise<PuzzleDetails> {
    const puzzleDetailsService = new FetchService(
      `/newapi/puzzle-details/${puzzleId}/`
    );

    return puzzleDetailsService.get<PuzzleDetails>().then((puzzleDetails) => {
      return puzzleDetails;
    });
  }
}

export const puzzleDetailsService = new PuzzleDetailsService();
