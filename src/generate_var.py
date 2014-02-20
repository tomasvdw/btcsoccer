#!/usr/bin/python

import os
import pystache

from datetime import date, datetime, timedelta
import dateutil.parser
import btcs
from decimal import Decimal

import simplejson as json

import logging
def modification_date(filename):
    t = os.path.getmtime(filename)
    return datetime.fromtimestamp(t)

# generate variadic files , key=lambda game: game['date'])/var

def render(template, data):
    "Renders a mustache template"
    renderer = pystache.Renderer()
    html = renderer.render_path('../templates/' + template, data)
    with open(btcs.path('var', template), "w") as f:
        f.write(html.encode('utf8'))

    logging.info('Written: ' + template)

def generate_pub():

    # load all active games in memory
    games = { game: json.loads(open(btcs.path('games/new',game),'r').read()) 
            for game 
            in  os.listdir(btcs.path('games/new', ''))}


    files = os.listdir(btcs.path('bets/received', '')) 
    slips = [ json.loads(open(btcs.path('bets/received',slip),'r').read()) 
            for slip 
            in files]


    for gameid, game in games.iteritems():

        game['results'] = [ { "away": a, "cols": [ {
                "score": 0 
            } for h in range(6) ] } for a in range(6) ]

        # sum all results found in bets

        for slip in slips:
            for bet in slip['bets']:
                if bet['game'] == gameid:
                    h,a = bet['result'].split('-')
                    h = int(h)
                    a = int(a)
                    am = int(Decimal(bet['amount']))
                    game['results'][a]['cols'][h]['score'] = (
                        game['results'][a]['cols'][h]['score'] + am)
                    game['total'] = game.get('total', 0) + am
                    


    # walk again through slips to generate account info
    accounts = {}
    for slip in slips:
        if not slip['accountid'] in accounts:
            accounts[slip['accountid']] = {}
        for bet in slip['bets']:
            if not bet['game'] in accounts[slip['accountid']]:
                accounts[slip['accountid']][bet['game']] = []

            accounts[slip['accountid']][bet['game']].append(bet)


    for (accountid, account) in accounts.iteritems():
        with open(btcs.path('var', accountid), 'w') as f:
            f.write(json.dumps(account, sort_keys=True, indent=4, separators=(',', ': ')))

    games = sorted(games.values(), key=lambda game: game['date'])

    # walk through games to generate data for templates
    for game in games:
        if game['time'][:1].isdigit():
            tm = int(game['time'][:-1])
            if tm >0 and tm < 46:
                game['status'] = '1st half'
            else:
                game['status'] = '2nd half'
        else:
            game['status'] = game['time']

        if 'result' in game:
            (game['home_score'], game['away_score']) = game['result'].split('-')



    # split in live/today/later
    now = datetime.utcnow()
    now = modification_date(btcs.path('cache', 'matches.xml'))

    maxtime_live = (now + timedelta(minutes = btcs.DEADLINE_MINS)).isoformat()
    maxtime_today = datetime(now.year, now.month, now.day, 23,59,59,0, None).isoformat()

    live  = [ game for game in games if game['date'] < maxtime_live]
    today = [ game for game in games if game['date'] >= maxtime_live and game['date'] < maxtime_today]
    later = [ game for game in games if game['date'] >= maxtime_today]

    later = later[:10]

    alldata = { 'games': { 'live': live, 'today': today, 'later': later } }
    
    render('games.html', alldata)

    #print(alldata)



if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)

    generate_pub()


