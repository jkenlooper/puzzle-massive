export class ChooseBitService {
  constructor() {}

  getBits(limit: number): Promise<string[]> {
    return fetch("/newapi/choose-bit/").then(function(response: Response) {
      if (!response.ok) {
        throw new Error(response.statusText);
      }
      return response.json().then((response: any) => {
        return response.data.slice(0, limit);
      });
    });
  }
}

export const chooseBitService = new ChooseBitService();
