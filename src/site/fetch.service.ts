class FetchService {
  url: string;

  constructor(url: string) {
    this.url = url;
  }

  get<T>(): Promise<T> {
    return fetch(this.url).then((response: Response) => {
      if (!response.ok) {
        throw new Error(response.statusText);
      }
      return response.json().then((response: T) => {
        return response;
      });
    });
  }
}

export default FetchService;
