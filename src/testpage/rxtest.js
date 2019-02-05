import {Observable} from 'rxjs/Observable'
import {Subject} from 'rxjs/Subject'

// patch the Observable with these operators
import 'rxjs/add/observable/of'
import 'rxjs/add/operator/map'

Observable.of(1, 2, 3).map(x => x + '!!!') // etc

const myObservable = new Subject()
myObservable.subscribe(value => console.log(value))
myObservable.next('foo')

class Test {
  constructor (_fetch) {
    this.fetch = _fetch
  }

  init () {
    console.log('init')
    this.fetch('http://localhost:4444/test.json')
      .then(function (response) {
        return response.json()
      })
      .then(function (myJson) {
        console.log(JSON.stringify(myJson, null, 2))
      })
      .catch((err) => {
        console.log(err)
      })
  }
}

const test = new Test(window.fetch)
test.init()
