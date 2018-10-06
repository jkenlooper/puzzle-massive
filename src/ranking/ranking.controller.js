export default class RankingController {
  constructor ($scope, rankingService) {
    let self = this
    self.playerRanks = []
    self.selectPlayerRanks = selectPlayerRanks
    let allPlayerRanks = []
    const playerID = Number($scope.userDetails.id)
    const range = 15
    self.playerRank
    self.totalActivePlayers = 0
    let offset = 0
    self.selectPlayerRanksUp = selectPlayerRanksUp
    self.selectPlayerRanksDown = selectPlayerRanksDown
    self.hasUp = false
    self.hasDown = false
    self.isReady = false

    init()

    function getPlayerRanks () {
      return rankingService.getRanks()
        .then(function (data) {
          let list = data.filter(isActivePlayer)
          self.playerRank = list.findIndex((item) => Number(item.id) === playerID) + 1
          return list
        })
    }

    function isActivePlayer (item) {
      return Number(item.id) === playerID || !(item.score === 0 || item.icon === '')
    }

    function setTopPlayers (item, index) {
      item.topPlayer = index < 15
      return item
    }

    function selectPlayerRanks (offset = 0) {
      let start = Math.max(((self.playerRank - 1) - offset) - (range / 2), 0)
      let end = Math.max(((self.playerRank - 1) - offset) + (range / 2), range)
      self.playerRanks = allPlayerRanks.slice(start, end)
      self.hasUp = start > 1
      self.hasDown = end < allPlayerRanks.length
    }

    function selectPlayerRanksUp () {
      offset = offset + range
      selectPlayerRanks(offset)
    }

    function selectPlayerRanksDown () {
      offset = offset - range
      selectPlayerRanks(offset)
    }

    function init () {
      getPlayerRanks()
        .then(function (data) {
          allPlayerRanks = data.map(setTopPlayers)
          self.totalActivePlayers = allPlayerRanks.length
          selectPlayerRanks()
          self.isReady = true
        })
    }
  }
}
RankingController.$inject = ['$scope', 'rankingService']
