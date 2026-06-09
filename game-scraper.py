from pathlib import Path
import pandas as pd
columns = ['PokemonName','DraftRoundNo','PlayerName','DraftedByPlayer','OpponentName','RegRound','PlayoffRound','GameNumber','Lead','TurnsIn','MovesUsed','Kills','Move1','Move2','Move3','Move4']
data = []

# Get all .txt files in the current directory
# Each txt file is a game transcript downloaded from PokemonShowdown
txt_files = [file.name for file in Path('.').glob('*.txt')]
print(txt_files)


# Loop through each game transcript
# Primary data structure is a dict of dicts
#   PlayerDict = {'PokemonName': PokemonDict}
#       PokemonDict = {'ColumnName': GameData}
# This allows for easy transcription as PokemonShowdown text is formatted differently for "player1" and "player2"
for filename in txt_files:
    with open(filename, "r", encoding="utf-8") as file:
        filetext = file.read()

    gameNo = filename.split('_')[1].split('.')[0]
    print(gameNo) # Track longer matches through file naming conventions

    # Separate each game by turn
    # Whitespace character is needed to avoid false positives for moves like "Flip Turn"
    turnsList = filetext.split(sep='Turn ')


    player1Pokemon = turnsList[0].split('\'s team')[1].split('\n')[1].split('/')
    player1Pokemon = [x.strip(' ') for x in player1Pokemon]
    player2Pokemon = turnsList[0].split('\'s team')[2].split('\n')[1].split('/')
    player2Pokemon = [x.strip(' ') for x in player2Pokemon]
    print(player1Pokemon,player2Pokemon)


    #print(turnsList[0].split('Go!'))

    # The first Pokemon set out has specific text flags, so they're noted separately
    # Pokemon with multiple forms use their specific name in (parentheses)
    #   Use those when available
    lead1 = turnsList[0].split('Go!')[1].split('!')[0].strip(' ')
    if '(' in lead1:
        lead1 = lead1.split('(')[1].split(')')[0]
    print(lead1)
    lead2 = turnsList[0].split('Go!')[1].split('!')[1].split('sent out ')[1]
    print(lead2)
    if '(' in lead2:
        lead2 = lead2.split('(')[1].split(')')[0]


    player1Dict = dict.fromkeys(player1Pokemon)
    player2Dict = dict.fromkeys(player2Pokemon)

    print(player1Dict, player2Dict)


    innerKeys = ['Lead','TurnsIn','MovesUsed','Kills','Move1','Move2','Move3','Move4']

    for pokemon in player1Pokemon:
        player1Dict[pokemon] = dict.fromkeys(innerKeys)
        player1Dict[pokemon]['Lead'] = False
        player1Dict[pokemon]['TurnsIn'] = 0
        player1Dict[pokemon]['MovesUsed'] = 0
        player1Dict[pokemon]['Kills'] = 0
    for pokemon in player2Pokemon:
        player2Dict[pokemon] = dict.fromkeys(innerKeys)
        player2Dict[pokemon]['Lead'] = False
        player2Dict[pokemon]['TurnsIn'] = 0
        player2Dict[pokemon]['MovesUsed'] = 0
        player2Dict[pokemon]['Kills'] = 0

    currentPokemon1 = lead1
    currentPokemon2 = lead2

    player1Dict[currentPokemon1]['Lead'] = True
    player2Dict[currentPokemon2]['Lead'] = True


    for turn in turnsList[1:]:
        # Handle annoying edge cases where the (parentheses) name gets overwritten in-game
        if currentPokemon1 == 'Floette':
            currentPokemon1 = 'Floette-Eternal'
        if currentPokemon2 == 'Floette':
            currentPokemon2 = 'Floette-Eternal'
        if currentPokemon1 == 'Mimikyu-Busted':
            currentPokemon1 = 'Mimikyu'
        if currentPokemon2 == 'Mimikyu-Busted':
            currentPokemon2 = 'Mimikyu'
        
        
        player1Dict[currentPokemon1]['TurnsIn'] += 1
        player2Dict[currentPokemon2]['TurnsIn'] += 1

        for line in turn.split('\n\n'):
            print(line,'\n','EOL')

            # Switches have different text for player1 and player2
            # Pokemon with multiple forms use their specific name in (parentheses)
            # Mega Pokemon have their original name before the parentheses
            #   Detect which situation is relevant
            # Update currentPokemon after each switch
            if 'Go! ' in line:
                switch = line.split('Go! ')
                currentPokemon1 = switch[1].split('!')[0].strip(' ')
                if '(' in currentPokemon1:
                    if '-Mega' in currentPokemon1:
                        currentPokemon1 = currentPokemon1.split('(')[0].strip(' ')
                    else:
                        currentPokemon1 = currentPokemon1.split('(')[1].split(')')[0]


            if 'sent out ' in line:
                switch = line.split('sent out ')
                currentPokemon2 = switch[1].split('!')[0].strip(' ')
                if '(' in currentPokemon2:
                    if '-Mega' in currentPokemon2:
                        currentPokemon2 = currentPokemon2.split('(')[0].strip(' ')
                    else:
                        currentPokemon2 = currentPokemon2.split('(')[1].split(')')[0]


            # Give credit for each fainted Pokemon
            # We use the 'EXP method' for attributing credit
            #   The current Pokemon gets credit for a fainting rather than the one responsible for the move
            #   These are typically equivalent outside of multi-turn moves (Future Sight, Toxic)
            if ('fainted!' in line) and ('The opposing' in line):
                player1Dict[currentPokemon1]['Kills'] += 1

            if ('fainted!' in line) and ('The opposing' not in line):
                player2Dict[currentPokemon2]['Kills'] += 1

            # Track move usage
            # The word "used" is the delimiter for moves used by both players
            # After detecting usage and isolating the moveName, assign the value to player1 or player2
            if ('used ' in line):
                moveUsageLines = line.split('\n') # The 1th index should include whether the move was NVE or SE (For future implementations)
                #print(moveUsageLines)
                for moveUsageLine in moveUsageLines:
                    if 'used ' in moveUsageLine:
                        break
                moveName = moveUsageLine.split('used ')[1].split('!')[0].strip(' ')
                print(moveUsageLine,'usageLINE')
                print(moveName,'MOVE')

                if 'The opposing' in moveUsageLine:
                    player2Dict[currentPokemon2]['MovesUsed'] += 1
                    
                    # Keep track of all moves revealed by a Pokemon
                    # Each MoveX data field will contain a list of [MoveName, NumberOfUses]
                    # Assign each new move to the next empty slot
                    # If move is already in the data, just increment the NumberOfUses
                    # Ignore the situation where a Pokemon uses more than 4 moves (May be needed if Z-Moves introduced)
                    for key in ['Move1','Move2','Move3','Move4']:
                        if player2Dict[currentPokemon2][key] is None:
                            player2Dict[currentPokemon2][key] = [moveName,1]
                            break
                        elif player2Dict[currentPokemon2][key][0] == moveName:
                            player2Dict[currentPokemon2][key][1] += 1
                            break
                else:
                    player1Dict[currentPokemon1]['MovesUsed'] += 1

                    for key in ['Move1','Move2','Move3','Move4']:
                        if player1Dict[currentPokemon1][key] is None:
                            player1Dict[currentPokemon1][key] = [moveName,1]
                            break
                        elif player1Dict[currentPokemon1][key][0] == moveName:
                            player1Dict[currentPokemon1][key][1] += 1
                            break


    print(player1Dict)
    print(player2Dict)

    # Iterate through each playerDict and export each Pokemon's information as a pandas DF row
    for pokemon in player1Dict:
        newRow = [pokemon,'','','','','','',gameNo,player1Dict[pokemon]['Lead'],player1Dict[pokemon]['TurnsIn'],player1Dict[pokemon]['MovesUsed'],player1Dict[pokemon]['Kills'],player1Dict[pokemon]['Move1'],player1Dict[pokemon]['Move2'],player1Dict[pokemon]['Move3'],player1Dict[pokemon]['Move4']]
        data.append(newRow)

    for pokemon in player2Dict:
        newRow = [pokemon,'','','','','','',gameNo,player2Dict[pokemon]['Lead'],player2Dict[pokemon]['TurnsIn'],player2Dict[pokemon]['MovesUsed'],player2Dict[pokemon]['Kills'],player2Dict[pokemon]['Move1'],player2Dict[pokemon]['Move2'],player2Dict[pokemon]['Move3'],player2Dict[pokemon]['Move4']]
        data.append(newRow)


# Export DF
gamesData = pd.DataFrame(data = data,columns = columns)
gamesData.to_csv('PokemonLeague_statsheet.csv',index=False)