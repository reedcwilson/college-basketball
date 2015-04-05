#!/usr/bin/env python

import sys
import os
import shutil
import urllib2

class Downloader:

    def __init__(self):
        pass

    def download(self, path):
        universities = os.listdir(path)
        cur_season = 1997
        seasons = cur_season - 1996
        i = cur_season
        for season in range(seasons):
            opener = urllib2.build_opener()
            folder = ('%s' % (i % 100)).zfill(2)
            opener.addheaders.append(('Cookie', 'sseason=%s' % folder))
            if os.path.exists(folder):
                shutil.rmtree(folder)
            os.mkdir(folder)
            for univ in universities:
                if not univ in os.listdir('%s' % (folder)):
                    try:
                        response = opener.open('http://www.bbstate.com/teams/%s/performances/team' % (univ))
                        with open('%s/%s' % (folder, univ), 'w') as f:
                            f.write(response.read())
                    except:
                        print 'failed to download: %s' % univ
            i -= 1


class Extractor:

    def __init__(self):
        pass

    def loop(self, path):
        filename = 'data.arff'
        if os.path.isfile(filename):
            os.remove('data.arff')
        for season in os.listdir(path):
            new_path = '%s/%s' % (path,season)
            for univ in os.listdir(new_path):
                stats = self.extract('%s/%s' % (new_path, univ))
                with open(filename, 'a') as f:
                    f.write(self.to_arff_data(season, univ, stats))

    # extracts the seasons/universities/games as individual dictionaries
    def get_seasons(self, path):
        seasons = {}
        # get all of the matchup data for each season
        for season in os.listdir(path):
            universities = {}
            new_path = '%s/%s' % (path,season)
            # get the university stats for the current season
            for univ in os.listdir(new_path):
                games = self.extract('%s/%s' % (new_path, univ))
                universities[univ] = games
            seasons[season] = universities
        return seasons

    # matches up teams based on their seasons averages per opponent
    def process_matchups(self, seasons):
        new_games = []
        for season_key, season in seasons.iteritems():
            for team_key, team in season.iteritems():
                # get the current team's average if they have games
                if len(team) > 0:
                    averages = self.get_season_averages(team)
                    # for every game that the team has
                    for game in team:
                        # only add to new_games if the opponent has data (division 1) and the opponent has games
                        if game['team'].upper() in season and len(season[game['team'].upper()]) > 0:
                            # find the opponents averages
                            opp_averages = self.get_season_averages(season[game['team'].upper()])
                            # the outcome here is actually the cur team's outcome but I'm sticking it on the opp 
                            # so it won't overwrite the average outcome every iteration
                            new_games.append((averages, opp_averages, game['outcome'], game['loc']))
        return new_games

    # writes the games out to a file
    def write_matchups(self, new_games):
        filename = 'data.arff'
        if os.path.isfile(filename):
            os.remove('data.arff')
        with open(filename, 'w') as f:
            f.write(self.to_matchup_arff_data(new_games))

    # writes the season averages out to a file
    def write_averages(self, averages):
        filename = 'data.arff'
        if os.path.isfile(filename):
            os.remove('data.arff')
        #for team_averages in averages:
            #print type(team_averages), team_averages
        with open(filename, 'a') as f:
            #f.write(self.to_arff_data('2015', team_averages['cur_team'], team_averages))
            f.write(self.to_arff_data('2015', averages))

    # get 2015 season averages
    def get_single_season_averages(self, season):
        averages = []
        for team_key, team in season.iteritems():
            # get the current team's average if they have games
            if len(team) > 0:
                team_averages = self.get_season_averages(team)
                team_averages['cur_team'] = team_key
                averages.append(team_averages)
        return averages

    # gets the season averages for the given team
    def get_season_averages(self, team):
        averages = {} 
        for stat_key in team[0]:
            if type(team[0][stat_key]) == float:
                averages[stat_key] = 0
            else:
                averages[stat_key] = ''
        # get the totals
        for game in team:
            for stat_key, stat in game.iteritems():
                if type(stat) == float:
                    if stat_key in averages:
                        averages[stat_key] += stat if not stat == '?' else 0
                    else:
                        averages[stat_key] = stat if not stat == '?' else 0
                else:
                    averages[stat_key] = stat if not stat == '?' else 0
        # divide totals by number of games to get averagess
        for stat_key, stat in averages.iteritems():
            if type(averages[stat_key]) == float:
                averages[stat_key] = stat / len(team)
        return averages


    def extract(self, path):
        games = []
        with open(path) as f:
            table = [ line.lower() for line in f.readlines() if '<table' in line.lower() ][0]
            tds = table.split('<td')
            base = 27
            for i in range(((len(tds)-1)/23)-1):
                game = {}
                # 24 first line, 47 second 70 third
                if 'href=' in tds[base]:
                    game['team']    =           tds[base].split('href=')[1].split('/')[2]
                else:
                    game['team'] = '?'
                game['loc'], game['outcome'] =      tds[base+1].split('>')[4][0:3].split('/')
                game['pf']      =           float(tds[base+2].split('<b>')[1].split('<')[0])
                game['pa']      =           float(tds[base+3].split('<b>')[1].split('<')[0])
                game['fgp']     =           float(tds[base+4].split('<br>')[1].split('<')[0])
                game['ftp']     =           float(tds[base+5].split('<br>')[1].split('<')[0])
                game['tpp']     =           float(tds[base+6].split('<br>')[1].split('<')[0])
                game['efgp']    =           float(tds[base+7].split('<br>')[1].split('<')[0])
                game['ppws']    =           float(tds[base+8].split('<br>')[1].split('<')[0])
                game['to_r']    =           float(tds[base+9].split('<br>')[1].split('<')[0])
                game['blk']     =           float(tds[base+10].split('<br>')[1].split('<')[0])
                game['f']       =           float(tds[base+11].split('<br>')[1].split('<')[0])
                game['offr']    =           float(tds[base+12].split('<br>')[1].split('<')[0])
                game['tr']      =           float(tds[base+13].split('<br>')[1].split('<')[0])
                game['stl']     =           float(tds[base+14].split('<br>')[1].split('<')[0])
                game['a']       =           float(tds[base+15].split('<br>')[1].split('<')[0])
                # if we can't figure out the possession then save as a question mark
                poss            =           tds[base+16].split('<br>')[1].split('>')[1].split('<')[0]
                game['poss']    =           float(poss) if poss.strip() else '?'
                game['o_ppp']   =           float(tds[base+17].split('<br>')[1].split('<')[0])
                game['d_ppp']   =           float(tds[base+18].split('<br>')[1].split('<')[0])
                games.append(game)
                base += 23
        return games

    #def to_arff_data(self, season, univ, stats):
    def to_arff_data(self, season, stats):
        result = ''
        for stat in stats:
            result += '%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\n' % \
                    (season, stat['cur_team'], stat['team'], stat['loc'], stat['pf'], stat['pa'], \
                    stat['fgp'], stat['ftp'], stat['tpp'], stat['efgp'], stat['ppws'], \
                    stat['to_r'], stat['blk'], stat['f'], stat['offr'], stat['tr'], stat['stl'], \
                    stat['a'], stat['poss'], stat['o_ppp'], stat['d_ppp'], stat['outcome'])
            #result += '%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\n' % \
                    #(stat['loc'], stat['pf'], stat['pa'], \
                    #stat['fgp'], stat['ftp'], stat['tpp'], stat['efgp'], stat['ppws'], \
                    #stat['to_r'], stat['blk'], stat['f'], stat['offr'], stat['tr'], stat['stl'], \
                    #stat['a'], stat['poss'], stat['o_ppp'], stat['d_ppp'],stat['outcome'])
        return result

    def to_matchup_arff_data(self, games):
        result = ''
        for team, opp, outcome, loc in games:
            result += '%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\n' % \
                    (loc, team['pf'], team['pa'], team['fgp'], team['ftp'], team['tpp'], team['efgp'], team['ppws'], team['to_r'], team['blk'], team['f'], team['offr'], team['tr'], team['stl'], team['a'], team['poss'], team['o_ppp'], team['d_ppp'], 
                    opp['pf'], opp['pa'], opp['fgp'], opp['ftp'], opp['tpp'], opp['efgp'], opp['ppws'], opp['to_r'], opp['blk'], opp['f'], opp['offr'], opp['tr'], opp['stl'], opp['a'], opp['poss'], opp['o_ppp'], opp['d_ppp'], outcome)
        return result




if __name__ == '__main__':
    # Extract All Games
    #extractor = Extractor()
    #extractor.loop(sys.argv[1])

    # Extract All Games
    #extractor = Extractor()
    #seasons = extractor.get_seasons(sys.argv[1])
    #games = extractor.process_matchups(seasons)
    #extractor.write_matchups(games)

    # Extract 2015 Season Averages
    extractor = Extractor()
    season_2015 = extractor.get_seasons(sys.argv[1])['15']
    averages = extractor.get_single_season_averages(season_2015)
    extractor.write_averages(averages)

    # Download
    #downloader = Downloader()
    #downloader.download(sys.argv[1])

# vim: set sw=4 sts=4 ts=4 noai :
