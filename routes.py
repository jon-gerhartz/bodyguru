from flask import Blueprint, render_template, request, redirect, url_for, flash

main = Blueprint('main', __name__)

nyy_line = 'NYY to win -250'
nym_line = 'NYM to win -100'
bets = {'nyy':nyy_line, 'nym': nym_line}

scores = [
	{'home_team':'nyy', 'home_score': 5, 'away_team': 'cin', 'away_score': 1},
	{'home_team':'nym', 'home_score': 7, 'away_team': 'atl', 'away_score': 5},
	{'home_team':'tb', 'home_score': 3, 'away_team': 'bos', 'away_score': 4},
	{'home_team':'min', 'home_score': 6, 'away_team': 'mil', 'away_score': 4},
	{'home_team':'lad', 'home_score': 5, 'away_team': 'sf', 'away_score': 1},
	{'home_team':'tor', 'home_score': 7, 'away_team': 'bal', 'away_score': 5},
	{'home_team':'phi', 'home_score': 3, 'away_team': 'laa', 'away_score': 4},
	{'home_team':'chw', 'home_score': 6, 'away_team': 'chi', 'away_score': 4},
	{'home_team':'nyy', 'home_score': 5, 'away_team': 'cin', 'away_score': 1},
	{'home_team':'nym', 'home_score': 7, 'away_team': 'atl', 'away_score': 5},
	{'home_team':'tb', 'home_score': 3, 'away_team': 'bos', 'away_score': 4},
	{'home_team':'min', 'home_score': 6, 'away_team': 'mil', 'away_score': 4},
	{'home_team':'lad', 'home_score': 5, 'away_team': 'sf', 'away_score': 1},
	{'home_team':'tor', 'home_score': 7, 'away_team': 'bal', 'away_score': 5},
	{'home_team':'phi', 'home_score': 3, 'away_team': 'laa', 'away_score': 4},
	{'home_team':'chw', 'home_score': 6, 'away_team': 'chi', 'away_score': 4},
	{'home_team':'nyy', 'home_score': 5, 'away_team': 'cin', 'away_score': 1},
	{'home_team':'nym', 'home_score': 7, 'away_team': 'atl', 'away_score': 5},
	{'home_team':'tb', 'home_score': 3, 'away_team': 'bos', 'away_score': 4},
	{'home_team':'min', 'home_score': 6, 'away_team': 'mil', 'away_score': 4},
	{'home_team':'lad', 'home_score': 5, 'away_team': 'sf', 'away_score': 1},
	{'home_team':'tor', 'home_score': 7, 'away_team': 'bal', 'away_score': 5},
	{'home_team':'phi', 'home_score': 3, 'away_team': 'laa', 'away_score': 4},
	{'home_team':'chw', 'home_score': 6, 'away_team': 'chi', 'away_score': 4}
	]

@main.route('/bets', methods=['GET', 'POST'])
def index():
	return render_template('index.html', bets=bets, scores=scores)

@main.route('/bets/<line>', methods=['GET', 'POST'])
def line_page(line):
	bet_line = bets[line]
	line_details = bet_line + '/n details here'
	return render_template('line.html', line_details=line_details)