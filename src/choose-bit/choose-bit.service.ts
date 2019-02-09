interface Response {
  statusText: string;
  ok: boolean;
  json: Function;
}

export class ChooseBitService {
  private fetch: any;
  constructor(_fetch: any) {
    this.fetch = _fetch.bind(window);
  }

  getBits(limit: number): Promise<string[]> {
    return this.fetch("/newapi/choose-bit/").then(function(response: Response) {
      if (!response.ok) {
        throw new Error(response.statusText);
      }
      const bits = response.json();
      return bits.slice(0, limit);
    });
  }
}

export const chooseBitService = new ChooseBitService(window.fetch);
