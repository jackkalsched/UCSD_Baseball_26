import pandas as pd 
import numpy as np 
import os 

# Using MLB probabilities for extra base advancements
second_to_home_single = 0.6085
first_to_third_single = 0.3184
first_to_home_double = 0.4047

def generate_base_out_state(df):

    # initialize new baserunner columns
    for i in [1, 2, 3]:
        df[f"runner_on_{i}"] = None

    rows = []
    runner_on_1, runner_on_2, runner_on_3 = None, None, None
    last_half_inning = None  # track when the half-inning changes

    def advance_runners(runners, batter=None, bases=1):
        """
        Advance runners by X bases and optionally place batter on base.
        Handles HR by ignoring batter placement if bases==4.
        """
        r1, r2, r3 = runners

        # advance existing runners
        for _ in range(bases):
            if r3 is not None: # runner on 3rd
                r3 = None
            r3, r2, r1 = r2, r1, None

        # put batter on base (if not HR)
        if batter is not None and bases < 4:
            if bases == 1:
                r1 = batter
            elif bases == 2:
                r2 = batter
            elif bases == 3:
                r3 = batter

        return [r1, r2, r3]

    for _, row in df.iterrows():
        hit_type = str(row['PlayResult']).lower()
        tagged_hit_type = str(row['TaggedHitType']).lower()
        k_or_bb = row['KorBB']
        batter = row['Batter']
        half_inning = f"{row['Inning']}{row['Top_Bottom']}"

        # reset bases on new half-inning
        if half_inning != last_half_inning:
            runner_on_1, runner_on_2, runner_on_3 = None, None, None

        runners = [runner_on_1, runner_on_2, runner_on_3]

        # ------------------ Event handling ------------------
        if hit_type == 'single':
            if tagged_hit_type != 'bunt':
                if runner_on_2 is None:
                    runners = advance_runners(runners, batter=batter, bases=1)
                else:
                    if np.random.rand() < second_to_home_single:  ## runner scores from second
                        if np.random.rand() < first_to_third_single: ## runner goes from first to third
                            if runner_on_3 is not None:
                                runners[2] = runners[0] 
                                runners[1] = None
                                runners[0] = batter
                        else:
                            runners[1] = runners[0]
                            runners[0] = batter
                    else: ## runner on 2nd didn't score on the single, no run scores
                        runners = advance_runners(runners, batter=batter, bases=1)
            else:  # bunt single
                if runners[2] is None:
                    runners = advance_runners(runners, batter=batter, bases=1)
                elif all(runners):  # bases loaded bunt
                    runners = advance_runners(runners, batter=batter, bases=1)
                else:
                    runners[0] = batter

        elif hit_type == 'double':
            runners = advance_runners(runners, batter=batter, bases=2)
            if runner_on_1 is not None and np.random.rand() < first_to_home_double:
                runners[2] = None  # runner on first scored

        elif hit_type == 'triple':
            runners = advance_runners(runners, batter=batter, bases=3)

        elif hit_type in ['homerun', 'home run']:
            runners = [None, None, None]  # clear bases

        elif k_or_bb == 'Walk':
            # force advance if bases are occupied
            if runners[0] is None:
                runners[0] = batter
            elif runners[1] is None:
                runners[1], runners[0] = runners[0], batter
            elif runners[2] is None:
                runners[2], runners[1], runners[0] = runners[1], runners[0], batter
            else:  # bases loaded walk
                runners[2], runners[1], runners[0] = runners[1], runners[0], batter

        elif hit_type == 'fielderschoice':
            if runners[0]:
                if runners[1] and runners[2]:  # bases loaded
                    runners[2], runners[1], runners[0] = runners[1], runners[0], batter
                elif runners[1]:  # 1st & 2nd
                    runners[1], runners[0] = runners[0], batter
                elif runners[2]: # 1st & 3rd, assuming attempting double play / force at second
                    runners[2], runners[0] = None, batter
                else:  # just 1st
                    runners[0] = batter
            elif runners[1]:
                runners[0], runners[1] = batter, None
            elif runners[2]:
                runners[0], runners[2] = batter, None
            else:
                runners[0] = batter

        elif hit_type == 'stolenbase':
            if runners[0] and not runners[1]:      # steal 2nd
                runners[1], runners[0] = runners[0], None
            elif runners[0] and runners[1]:        # double steal
                runners[2], runners[1], runners[0] = runners[1], runners[0], None
            elif not runners[0] and runners[1]:    # steal 3rd
                runners[2], runners[1] = runners[1], None
            elif runners[2] and runners[1] and not runners[0]: # only play i can confidently logic that the guy steals home (2nd and 3rd)
                runners[2] = runners[1]

        elif hit_type == 'caughtstealing':
            if runners[0] and not runners[1]:
                runners[0] = None
            elif runners[0] and runners[1]:
                runners[1], runners[0] = runners[0], None
            elif not runners[0] and runners[1]:
                runners[1] = None

        elif hit_type == 'error':
            runners = advance_runners(runners, batter=batter, bases=1)

        elif hit_type == 'sacrifice':
            runners = advance_runners(runners)
            runners[0] = None

        elif hit_type == 'out':
            if tagged_hit_type == 'groundball':
                if runners[1] and runners[2]:       # 2 & 3
                    runners = advance_runners(runners, bases=1)
                    runners[0] = None
                elif not runners[1] and runners[2]: # just 3rd
                    runners[2] = None
                    runners[0] = None
                elif runners[1] and not runners[2]: # just 2nd
                    runners[0] = None
            # else: do nothing for other outs
        # ---------------------------------------------------

        # save updated state
        runner_on_1, runner_on_2, runner_on_3 = runners
        row['runner_on_1'], row['runner_on_2'], row['runner_on_3'] = runners
        rows.append(row)
        last_half_inning = half_inning

    result = pd.DataFrame(rows) 
    
    # shift runners down one row
    result['runner_on_1'] = result['runner_on_1'].shift(1)
    result['runner_on_2'] = result['runner_on_2'].shift(1)
    result['runner_on_3'] = result['runner_on_3'].shift(1)
    
    # identify half inning
    result['half_inning'] = (result['Inning'].astype(str) + result['Top_Bottom'])
    result['different_half_inning'] = (result['half_inning'] != result['half_inning'].shift(1))
    result.loc[result['different_half_inning'] == True, ['runner_on_1', 'runner_on_2', 'runner_on_3']] = [None, None, None] 
    
    # encode baserunner base occupation
    result['first_base'] = (result['runner_on_1'].notna()) * 1
    result['second_base'] = (result['runner_on_2'].notna()) * 1
    result['third_base'] = (result['runner_on_3'].notna()) * 1

    # concatenate baseout state
    result['base_count_state'] = (
        result[['first_base', 'second_base', 'third_base', 'Balls', 'Strikes']].astype(str).agg("_".join, axis = 1)
    )
    
    csv_name = 're288.csv'
    
    # check if file exists in current working directory
    if os.path.exists(csv_name):
        re288 = pd.read_csv(csv_name)
    else:
        # fall back to script directory
        re288 = pd.read_csv(os.path.join(os.path.dirname(__file__), csv_name))    
    
    with_re288 = result.merge(re288, on = ['base_count_state', 'Outs'], how = 'left')
    with_re288['delta_run_exp'] = with_re288['average_runs_scored'] - (with_re288['average_runs_scored'].shift(1))
    with_re288 = with_re288.rename(columns = {'average_runs_scored': 'expected_runs_remaining'})
    
    return with_re288
    
    