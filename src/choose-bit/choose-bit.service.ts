interface Response {
  statusText: string;
  ok: boolean;
  json: Function;
}

export class ChooseBitService {
  //private fetch: any;
  constructor() {
    //this.fetch = _fetch.bind(window);
  }

  getBits(limit: number): Promise<string[]> {
    return fetch("/newapi/choose-bit/").then(function(response: Response) {
      if (!response.ok) {
        throw new Error(response.statusText);
      }
      return response.json().then((response: any) => {
        console.log("bits", response);
        return response.data.slice(0, limit);
      });
    });
  }
}

export const chooseBitService = new ChooseBitService();
