#!/usr/bin/env python2.7

"""
Denyven Peng Uni: dsp2124 Version
Basketball Betting Test
"""

# Imports, configuation and setting up template directory 
# Code from CSW4111 server.py example
import os
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, g, redirect, Response, session, flash, url_for
from random import randint

DATABASEURI = "postgresql://dsp2124:Nerfroom1@w4111vm.eastus.cloudapp.azure.com/w4111"
DEBUG = True
SECRET_KEY = 'development key'

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)
app.config.from_object(__name__)

engine = create_engine(app.config['DATABASEURI'])

games = engine.execute('''SELECT T1.t_name, T2.t_name, P.game_date, P.home_score, P.away_score, P.home_team_id, P.away_team_id
						  FROM teams T1, teams T2, played P
						  WHERE P.home_team_id = T1.team_id
						  AND P.away_team_id = T2.team_id''')
gameList = []
for row in games:
	for item in row:
		item = str.split(str(item))[0]
	gameList.append(row)

games.close()
game = None

username = None

# Code from CSW4111 server.py example
@app.before_request
def before_request():
  """
  This function is run at the beginning of every web request 
  (every time you enter an address in the web browser).
  We use it to setup a database connection that can be used throughout the request.

  The variable g is globally accessible.
  """
  try:
    g.conn = engine.connect()
  except:
    print "uh oh, problem connecting to database"
    import traceback; traceback.print_exc()
    g.conn = None

# Code from CSW4111 server.py example
@app.teardown_request
def teardown_request(exception):
  """
  At the end of the web request, this makes sure to close the database connection.
  If you don't, the database could run out of memory!
  """
  try:
    g.conn.close()
  except Exception as e:
    pass

@app.route('/')
def index():
	return render_template("index2.html")

# Code Inspired by Flask Tutorial Flaskr Code
@app.route('/login', methods=['GET', 'POST'])
def login():

	global username

	error = None

	if request.method == 'POST':
		
		# Check if username already exists
		result = engine.execute("SELECT COUNT(*) FROM users U WHERE U.username = %s",
						  	  request.form['username'])
		userExists = (result.fetchone()[0] != long(0))
		result.close()

		if not userExists:
			error = 'Invalid Username'
		if userExists:
			# Get Password of User
			result = engine.execute('SELECT pass FROM users U WHERE U.username = %s',
								     request.form['username'])
			password = str.split(str(result.fetchone()['pass']))[0]
			result.close()

			if request.form['password'] != password:
				error = 'Invalid Password'
			else:
				session['logged_in'] = True
				username = request.form['username']
				flash('Login Complete')
				return redirect(url_for('index'))

	return render_template('login.html', error=error)

# Code Inspired by Flask Tutorial Flaskr Code
@app.route('/logout')
def logout():

	global username 

	session.pop('logged_in', None)
	username = None
	flash('User Logged Out')
	return redirect(url_for('index'))

@app.route('/create_account', methods=['GET', 'POST'])
def create_account():
	error = None
	if request.method == 'POST':

		# Check if username already exists
		result = engine.execute('SELECT COUNT(*) FROM users U WHERE U.username = %s',
							  [request.form['username']])
		userExists = (result.fetchone()[0] != 0)
		result.close()

		# Check if email already exisits
		result = engine.execute('SELECT COUNT(*) FROM users U WHERE U.email = %s',
							[request.form['email']])
		emailExists = (result.fetchone()[0] != 0)
		result.close()

		if request.form['password'] != request.form['passwordConf']:
			error = 'Passwords Do Not Match'
		elif userExists:
			error = 'Username Already Exists'
		elif emailExists: 
			error = 'Email Aready Exists'
		else:
			engine.execute('INSERT INTO users VALUES (%s, %s, %s, current_date, 1000, 0, 0, 0)',
						 [request.form['username'], request.form['email'], request.form['password']])
			session['logged_in'] = True
			flash('Account Created')
			return redirect(url_for('index'))
	return render_template('create_account.html', error=error)

@app.route('/player_lookup', methods=['GET', 'POST'])
def player_lookup():
	error = None
	if request.method == 'POST':

		# Check if Player Exists
		result = engine.execute('SELECT COUNT(*) FROM players P WHERE P.p_name LIKE %s',
								'%' + request.form['pname'] + '%')

		playersExist = (result.fetchone()[0] != 0)
		result.close()

		context = dict(playersExist=playersExist, error=error)

		if not playersExist:
			error = 'Search Returned No Players'

			context["error"] = error

			return render_template('player_lookup.html', **context)
		
		if playersExist:

			result = g.conn.execute('''SELECT p_name, pos, pre_draft_team, years_of_service, draft_status, age 
									   FROM players P WHERE P.p_name LIKE %s''',
									   '%' + request.form['pname'] + '%')
			playerInfo = []
			for row in result:
				for item in row:
					item = str.split(str(item))[0]
				playerInfo.append(row)

			context["playerInfo"] = playerInfo

			return render_template('player_lookup.html', **context)
	return render_template('player_lookup.html')

@app.route('/team_lookup', methods=['GET', 'POST'])
def team_lookup():
	error = None
	if request.method == 'POST':
		
		# Check if Team Exists
		result = g.conn.execute('''SELECT COUNT(*)
								   FROM teams T
								   WHERE T.t_name LIKE %s''',
								   '%' + request.form['tname'] + '%')

		teamsExist = (result.fetchone()[0] != 0)

		context = dict(teamsExist=teamsExist, error=error)

		if not teamsExist:
			error = 'Search Returned No Teams'
			context["error"] = error

			return render_template('team_lookup.html', **context)

		if teamsExist:

			# If Season is Blank Default to 2016
			if request.form['season'] == '':
				season = 2016
			else:
				season = int(request.form['season'])

			context['season'] = season
			
			# Check if Season Exists
			result = g.conn.execute('''SELECT COUNT(*)
									   FROM seasons S 
									   WHERE S.s_year = %s''',
									   season)
			seasonExist = (result.fetchone()[0] != 0)

			if not seasonExist:
				error = 'Search Returned No Teams: Invalid Season'
				context['error'] = error

				return render_template('team_lookup.html', **context)

			if seasonExist:

				result = g.conn.execute('''SELECT T.T_name,T.wins,T.Losses,T.FG_Made,T.Three_Pt_Made
							   FROM teams T
							   WHERE T.t_name LIKE %s AND T.Season = %s''',
							   ['%' + request.form['tname'] + '%', season])

				teamInfo = []
				for row in result:
					for item in row:
						item = str.split(str(item))[0]
					teamInfo.append(row)

				context['teamInfo'] = teamInfo

				return render_template('team_lookup.html', **context)
	return render_template('team_lookup.html')


@app.route('/show_emails')
def show_emails():
	cursor = g.conn.execute("""SELECT email FROM users""")
	emails = []
	for result in cursor:
		emails.append(str.split(str(result['email']))[0])
	cursor.close()

	context = dict(data = emails)
	return render_template("show_emails.html", **context)

@app.route('/game_lookup', methods=['GET', 'POST'])
def game_lookup():
	error = None
	if request.method == 'POST':

		# Check if Team has played any home games
		result = g.conn.execute('''SELECT COUNT(*)
								   FROM teams T, played P
								   WHERE P.home_team_id = T.team_id AND T.t_name LIKE %s''',
								   '%' + request.form['tname'] + '%')

		teamsPlayed = (result.fetchone()[0] != 0)

		context = dict(teamsPlayed=teamsPlayed, error=error)

		if not teamsPlayed:
			error = "Team Does Not Exist or Hasn't Played Any Home Games"
			context["error"] = error

			return render_template('game_lookup.html', **context)

		if teamsPlayed:

			result = g.conn.execute('''SELECT T1.t_name, T2.t_name, P.game_date, P.home_score, P.away_score
								       FROM teams T1, teams T2, played P
								       WHERE P.home_team_id = T1.team_id
								   	   AND P.away_team_id = T2.team_id
								       AND T1.t_name LIKE %s''',
								       '%' + request.form['tname'] + '%')

			gameInfo = []
			for row in result:
				for item in row:
					item = str.split(str(item))[0]
				gameInfo.append(row)

			print(gameInfo)

			context['gameInfo'] = gameInfo
			return render_template('game_lookup.html', **context)
	return render_template('game_lookup.html')								

@app.route('/game_bet', methods=['GET', 'POST'])
def game_bet():

	global game
	global username

	if request.method == 'POST':

		result = g.conn.execute('''SELECT MAX(bet_id_game) FROM game_bet''')
		topBetID = result.fetchone()[0]

		newBetID = topBetID + 1
		homeID = game[5]
		gameDate = game[2]

		g.conn.execute('''INSERT INTO game_bet
						  VALUES (%s, %s, NULL, %s, %s)''',
						  [newBetID, username, homeID, gameDate])

		homeScore = game[3]
		awayScore = game[4]

		context = dict(betComplete=True, game=game)

		if request.form['bet'] == 'Home':
			if homeScore > awayScore:
				context["win"] = True
			elif homeScore < awayScore:
				context["win"] = False

		elif request.form['bet'] == 'Away':
			if homeScore > awayScore:
				context["win"] = False
			elif homeScore < awayScore:
				context["win"] = True

		print('betComplete:', context['betComplete'])
		print('Win:', context["win"])

		return render_template('game_bet.html', **context)

	randomGame = randint(0,39)
	game = gameList[randomGame]

	context = dict(game=game)
	return render_template('game_bet.html', **context)

# Initialization Code from CSW4111 server.py example
if __name__ == "__main__":
  import click

  @click.command()
  @click.option('--debug', is_flag=True)
  @click.option('--threaded', is_flag=True)
  @click.argument('HOST', default='0.0.0.0')
  @click.argument('PORT', default=8111, type=int)
  def run(debug, threaded, host, port):
    """
    This function handles command line parameters.
    Run the server using:

        python server.py

    Show the help text using:

        python server.py --help

    """

    HOST, PORT = host, port
    print "running on %s:%d" % (HOST, PORT)
    app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)


  run()