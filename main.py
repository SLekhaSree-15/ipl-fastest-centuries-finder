from flask import Flask, render_template, request, redirect, url_for, flash
import pandas as pd
from collections import defaultdict, deque

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Use an environment variable in production

combined_df = None

def build_graph(df):
    """Builds a graph from the DataFrame."""
    graph = defaultdict(list)
    for _, row in df.iterrows():
        player = row['Player']
        opponent = row['Against']
        graph[player].append(opponent)
        graph[opponent].append(player)
    return graph

def bfs_find_centuries(df, player_name=None):
    """Finds players who scored centuries using BFS."""
    graph = build_graph(df)
    centuries = []
    visited = set()

    # Normalize player names for case-insensitive comparison
    normalized_df = df.copy()
    normalized_df['Player'] = normalized_df['Player'].str.lower()

    # Start BFS from the specified player or all players
    if player_name:
        start_player = player_name.lower()
        if start_player not in normalized_df['Player'].values:
            return centuries  # If the player does not exist, return empty list
        start_nodes = [start_player]
    else:
        start_nodes = normalized_df['Player'].unique()

    queue = deque(start_nodes)

    while queue:
        current_player = queue.popleft()

        if current_player not in visited:
            visited.add(current_player)

            # Check for centuries for the current player
            player_data = normalized_df[normalized_df['Player'] == current_player]
            centuries_data = player_data[(player_data['Runs'] >= 100) & (player_data['BF'] < 50)]

            for _, match_row in centuries_data.iterrows():
                centuries.append({
                    'Player': match_row['Player'].title(),
                    'Opponent': match_row['Against'],
                    'Runs': match_row['Runs'],
                    'Balls Faced': match_row['BF'],
                    'Venue': match_row['Venue'],
                    'Year': match_row['Match Date'].split()[-1]
                })

            # Enqueue neighbors (exploring current player's connections)
            for neighbor in graph[current_player]:
                if neighbor not in visited:
                    queue.append(neighbor)

    return centuries

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_files():
    global combined_df
    files = request.files.getlist('files[]')
    dataframes = []

    for file in files:
        try:
            df = pd.read_csv(file)
            dataframes.append(df)
        except Exception as e:
            flash(f"Oh no! Couldn't read {file.filename}. Did a cat sit on your keyboard? 🤔 Error: {str(e)}", "error")
            return redirect(url_for('index'))

    if dataframes:
        combined_df = pd.concat(dataframes, ignore_index=True)
        flash('Files uploaded successfully! 🎉 Let’s find some centuries! ⚾️')
    else:
        flash('Oops! No files uploaded. Let’s try this again, champ!', 'error')

    return redirect(url_for('index'))

@app.route('/bfs', methods=['POST'])
def bfs_performance():
    global combined_df
    if combined_df is None:
        flash("Hey buddy! No data available. Please upload files first! 🥺", "error")
        return redirect(url_for('index'))

    sort_by = request.form.get('sort_by', 'runs')
    player_name = request.form.get('player_name')
    result = bfs_find_centuries(combined_df, player_name)

    valid_sort_columns = {'runs': 'Runs', 'balls': 'Balls Faced'}
    if sort_by not in valid_sort_columns:
        sort_by = 'runs'

    result.sort(key=lambda x: x[valid_sort_columns[sort_by]], reverse=(sort_by == 'runs'))

    if not result:
        flash("Yikes! No results found for the specified player. Maybe next time, yaar! 🤷‍♂️", "error")

    return render_template('bfs_results.html', results=result, player_name=player_name)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000, debug=True)
