@app.route('/team')
def team():
  cursor = g.conn.execute('SELECT T.T_name,T.wins,T.Losses,T.FG_Made,T.Three_Pt_Made FROM Teams WHERE T.T_name = %s AND T.Season = %s',Teamname,Season)
  results = cursor.fechone()
  result = results[0]
  if result is None:
    return render_template(team.html, result = "Invalid Team name or Season")
  return render_template(team.html, result = result)


@app.route('/game')
def game():
  cursor = g.conn.execute('SELECT P.Score FROM Played P, Teams T WHERE T.T_name = %s AND P.Game_Date = %s',Teamname,Date)
  results = cursor.fechone()
  result = results[0]
  if result is None:
    return render_template(game.html,result = "Invalid team name or Date")
  return render_template(game.html,result = result)

@app.route('/bet')
def beforebet():
  from random import randint
  SelectedGameIndex = randint(0,TBD)
  cursor = g.conn.execute('SELECT Temp1.Game_Date,Temp1.T_name,Temp2.T_name FROM (Played p1 JOIN Team T ON p1.Home_Team_ID = T.Team_ID) Temp1, (Played p2 JOIN Team T ON p2.Away_Team_ID = T.Team_ID) Temp2 WHERE Temp1.Game_Date = Temp2.Game_Date AND Temp1.Home_Team_ID = Temp2.Home_Team_ID')
  results = cursor.fetchon()
  result = results[SelectedGameIndex]
  date = result[0]
  home_team = result[1]
  away_team = result[2]
  return render_template(bet.html,Game_Info = date,Home_Team = home_team,Away_Team = away_team)

def afterbet():
