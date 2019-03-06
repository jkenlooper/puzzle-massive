interface PieceOrigin {
  x: number;
  y: number;
  r: number;
}
declare class PuzzleService {
  constructor(puzzleid: string | null, divulgerService: any);
  nextPieceMovementId: number;
  pieces(): any; // reqwest
  token(piece: number, mark: string): number;
  cancelMove(id: number, origin: PieceOrigin, pieceMovementId: number): void;
  move(
    id: number,
    x: number,
    y: number,
    r: number,
    origin: PieceOrigin,
    pieceMovementId: number
  ): void;
  processNextPieceMovement(): void;
}

export = PuzzleService;
