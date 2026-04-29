"""
TrackMan team code → full school name mapping.

Usage:
    from analytics_suite.team_codes import get_team_name, normalize_teams

    name = get_team_name("CSD_TRI")          # "UC San Diego"
    df["BatterTeam"] = normalize_teams(df["BatterTeam"])
"""

# Keys are TrackMan team codes; values are full school names.
# All codes verified via player roster lookups unless noted.
# Conferences continue to be added — unknown codes fall back to the raw code.
TEAM_NAMES: dict[str, str] = {

    # ══════════════════════════════════════════════════════════════════════
    # BIG EAST
    # ══════════════════════════════════════════════════════════════════════
    "BUT_BUL": "Butler",          # Bulldogs
    "CRE_BLU": "Creighton",       # Bluejays
    "GEO_HOY": "Georgetown",      # Hoyas
    "SET_PIR": "Seton Hall",      # Pirates
    "STJ_RED": "St. John's",      # Red Storm
    "UCO_HUS": "UConn",           # Huskies
    "VIL_WIL": "Villanova",       # Wildcats
    "XAV_MUS": "Xavier",          # Musketeers

    # ══════════════════════════════════════════════════════════════════════
    # BIG WEST
    # ══════════════════════════════════════════════════════════════════════
    "CSD_TRI": "UC San Diego",        # Tritons
    "CAL_AGO": "UC Davis",            # Aggies       (confirmed: player roster)
    "CAL_FUL": "Cal State Fullerton", # Titans
    "CAL_HIG": "UC Riverside",        # Highlanders  (confirmed: stadium/league)
    "CAL_MAT": "Cal State Northridge",# Matadors     (confirmed: stadium/league)
    "CAL_MUS": "Cal Poly SLO",        # Mustangs
    "CSU_BAK": "Cal State Bakersfield",# Roadrunners
    "HAW_WAR": "Hawaii",              # Warriors
    "LON_DIR": "Long Beach State",    # Dirtbags     (confirmed: BlairField)
    "SAN_GAU": "UC Santa Barbara",    # Gauchos      (confirmed: CaesarUyesaka)

    # ══════════════════════════════════════════════════════════════════════
    # SEC
    # ══════════════════════════════════════════════════════════════════════
    "ARK_RAZ": "Arkansas",        # Razorbacks
    "AUB_TIG": "Auburn",          # Tigers
    "FLA_GAT": "Florida",         # Gators
    "LSU_TIG": "LSU",             # Tigers
    "MIZ_TIG": "Missouri",        # Tigers
    "OLE_REB": "Ole Miss",        # Rebels
    "SOU_GAM": "South Carolina",  # Gamecocks
    "TEN_VOL": "Tennessee",       # Volunteers
    "TEX_A&M": "Texas A&M",       # Aggies
    "VAN_COM": "Vanderbilt",      # Commodores
    "ALA_CRI": "Alabama",         # Crimson Tide
    "KAN_JAY": "Kentucky",        # Wildcats  (KAN_JAY = Kentucky? verify — could be Kansas)
    "MIS_BEA": "Mississippi State",# Bulldogs
    "GEO_BUL": "Georgia",         # Bulldogs

    # ══════════════════════════════════════════════════════════════════════
    # ACC
    # ══════════════════════════════════════════════════════════════════════
    "BOC_EAG": "Boston College",  # Eagles       (confirmed: player roster)
    "DUK_BLU": "Duke",            # Blue Devils
    "FLA_SEM": "Florida State",   # Seminoles
    "GEO_TEC": "Georgia Tech",    # Yellow Jackets (verify code)
    "LOU_CAR": "Louisville",      # Cardinals
    "MIA_HUR": "Miami (FL)",      # Hurricanes
    "NOR_TAR": "North Carolina",  # Tar Heels
    "PIT_PAN": "Pittsburgh",      # Panthers
    "STA_CAR": "Stanford",        # Cardinal
    "SOU_TRO": "USC",             # Trojans       (Pac-12 → ACC)
    "UCLA":    "UCLA",             # Bruins        (Pac-12 → ACC)
    "VIR_CAV": "Virginia",        # Cavaliers
    "VIR_TEC": "Virginia Tech",   # Hokies
    "WAK_DEA": "Wake Forest",     # Demon Deacons
    "NOT_IRI": "Notre Dame",      # Fighting Irish (ACC)
    "CAL_BEA": "UC Berkeley",     # Golden Bears  (Pac-12 → ACC)
    "ORE_DUC": "Oregon",          # Ducks
    "ORE_BEA": "Oregon State",    # Beavers
    "WAS_HUS": "Washington",      # Huskies

    # ══════════════════════════════════════════════════════════════════════
    # BIG TEN
    # ══════════════════════════════════════════════════════════════════════
    "IU":      "Indiana",         # Hoosiers
    "MIC_WOL": "Michigan",        # Wolverines
    "MIN_GOL": "Minnesota",       # Golden Gophers
    "NEB":     "Nebraska",        # Cornhuskers
    "OSU_BUC": "Ohio State",      # Buckeyes
    "PEN_NIT": "Penn State",      # Nittany Lions
    "RUT_SCA": "Rutgers",         # Scarlet Knights

    # ══════════════════════════════════════════════════════════════════════
    # BIG 12
    # ══════════════════════════════════════════════════════════════════════
    "ARI_SUN": "Arizona State",   # Sun Devils
    "BYU_COU": "BYU",             # Cougars
    "KAN_WIL": "Kansas State",    # Wildcats      (confirmed: player roster)
    "OKL_COW": "Oklahoma State",  # Cowboys
    "OKL_SOO": "Oklahoma",        # Sooners
    "TCU_HFG": "TCU",             # Horned Frogs
    "TEX_LON": "Texas",           # Longhorns
    "TEX_RAI": "Texas Tech",      # Red Raiders   (confirmed: DanLawField)
    "UTA_UTE": "Utah",            # Utes
    "WAS_COU": "Washington State",# Cougars
    "TEX_A&M1":"Texas A&M",       # alt code

    # ══════════════════════════════════════════════════════════════════════
    # PAC-12 (remaining / pre-realignment codes)
    # ══════════════════════════════════════════════════════════════════════
    "ARI_CHR": "Arizona",         # Wildcats  (verify ARI_CHR)
    "COL_CUG": "Colorado",        # Buffaloes

    # ══════════════════════════════════════════════════════════════════════
    # ATLANTIC 10
    # ══════════════════════════════════════════════════════════════════════
    "DAY_FLY": "Dayton",          # Flyers
    "GEO_COL": "George Washington",# Colonials (verify)
    "RHO_RAM": "Rhode Island",    # Rams          (confirmed: player roster)
    "VCU_RAM": "VCU",             # Rams

    # ══════════════════════════════════════════════════════════════════════
    # AMERICAN ATHLETIC (AMER)
    # ══════════════════════════════════════════════════════════════════════
    "CIN_BEA": "Cincinnati",      # Bearcats
    "ECU_PIR": "East Carolina",   # Pirates
    "HOU_COU": "Houston",         # Cougars
    "SMU_SAI": "SMU",             # Mustangs  (verify)
    "SOU_BUL": "South Florida",   # Bulls     (verify)
    "UCF_KNI": "UCF",             # Knights
    "USF_BUL": "South Florida",   # Bulls
    "WIC_SHO": "Wichita State",   # Shockers  (verify)

    # ══════════════════════════════════════════════════════════════════════
    # MOUNTAIN WEST
    # ══════════════════════════════════════════════════════════════════════
    "AIR_FOR": "Air Force",       # Falcons
    "FRE_BUL": "Fresno State",    # Bulldogs
    "SAN_AZT": "San Diego State", # Aztecs
    "UNL_REB": "UNLV",            # Rebels

    # ══════════════════════════════════════════════════════════════════════
    # WEST COAST CONFERENCE
    # ══════════════════════════════════════════════════════════════════════
    "GON_BUL": "Gonzaga",         # Bulldogs
    "LOY_LIO": "Loyola Marymount",# Lions
    "PEP_WAV": "Pepperdine",      # Waves
    "SAN_BRO": "Santa Clara",     # Broncos       (confirmed: stadium/league)
    "SAN_DON": "San Francisco",   # Dons — USF    (confirmed: player roster)
    "SAN_TOR": "San Diego",       # Toreros — USD
    "STM_GAE": "Saint Mary's",    # Gaels

    # ══════════════════════════════════════════════════════════════════════
    # SUN BELT
    # ══════════════════════════════════════════════════════════════════════
    "APP_MOU": "Appalachian State",# Mountaineers
    "ARK_LIO": "Little Rock",     # Trojans   (verify)
    "GEO_SOU": "Georgia Southern",# Eagles
    "LOU_CAJ": "Louisiana",       # Ragin' Cajuns
    "SOU_ALA": "South Alabama",   # Jaguars   (verify)
    "TAM_SPA": "South Florida",   # Bulls     (verify — could be Tampa area team)
    "TEX_STA": "Texas State",     # Bobcats   (verify)
    "ULM_WAR": "UL Monroe",       # Warhawks

    # ══════════════════════════════════════════════════════════════════════
    # CONFERENCE USA
    # ══════════════════════════════════════════════════════════════════════
    "FLA_COL": "Florida International",# Panthers (verify)
    "FAU_OWL": "Florida Atlantic",# Owls
    "NMS_AGG": "New Mexico State",# Aggies
    "OLD_MON": "Old Dominion",    # Monarchs  (verify)
    "UAB_BLA": "UAB",             # Blazers
    "UNT_EAG": "North Texas",     # Mean Green (verify)
    "WES_KEN": "Western Kentucky",# Hilltoppers (verify)

    # ══════════════════════════════════════════════════════════════════════
    # AMERICA EAST
    # ══════════════════════════════════════════════════════════════════════
    "ALB_GRE": "Albany",          # Great Danes   (confirmed: player roster)
    "MAI_BLA": "Maine",           # Black Bears
    "NJI_HIG": "NJIT",            # Highlanders
    "UMA_AMH": "UMass Amherst",   # Minutemen
    "UMBC_RET": "UMBC",           # Retrievers

    # ══════════════════════════════════════════════════════════════════════
    # ATLANTIC SUN (ASUN)
    # ══════════════════════════════════════════════════════════════════════
    "SOU_IND16": "Southern Indiana",# Screaming Eagles (confirmed: player roster)
    "LIB_FLA": "Liberty",         # Flames
    "NOR_FLO": "North Florida",   # Ospreys   (verify)
    "NOF_OSP": "North Florida",   # Ospreys
    "STE_HAT": "Stetson",         # Hatters

    # ══════════════════════════════════════════════════════════════════════
    # BIG SOUTH
    # ══════════════════════════════════════════════════════════════════════
    "NCA_BUL": "UNC Asheville",   # Bulldogs      (confirmed: player roster)
    "CAM_CAM": "Campbell",        # Camels    (verify)
    "CHR_BRO": "Charleston Southern",# Buccaneers (verify)
    "GAS_COL": "Gardner-Webb",    # Runnin' Bulldogs (verify)
    "WIN_BUL": "Winthrop",        # Eagles    (verify — WIN_BUL or WIN_EAG?)
    "PRE_BLH": "Presbyterian",    # Blue Hose

    # ══════════════════════════════════════════════════════════════════════
    # CAA (Coastal Athletic Association)
    # ══════════════════════════════════════════════════════════════════════
    "DEL_HOR": "Delaware State",  # Hornets       (confirmed: player roster)
    "HOF_PRI": "Hofstra",         # Pride
    "NOR_HUS": "Northeastern",    # Huskies
    "WIL_CAR": "William & Mary",  # Tribe

    # ══════════════════════════════════════════════════════════════════════
    # MAAC
    # ══════════════════════════════════════════════════════════════════════
    "FAI_STA": "Fairfield",       # Stags
    "ION_GAE": "Iona",            # Gaels
    "MAR_RED": "Marist",          # Red Foxes     (confirmed: player roster)
    "MON_HAW": "Monmouth",        # Hawks
    "QUI_BOB": "Quinnipiac",      # Bobcats
    "RID_BRO": "Rider",           # Broncs
    "SPU_PEA": "Saint Peter's",   # Peacocks      (confirmed: player roster)

    # ══════════════════════════════════════════════════════════════════════
    # MAC (Mid-American)
    # ══════════════════════════════════════════════════════════════════════
    "AKR_ZIP": "Akron",           # Zips
    "BAL_CAR": "Ball State",      # Cardinals
    "BOW_COL": "Bowling Green",   # Falcons   (verify)
    "EMU_EAG": "Eastern Michigan",# Eagles
    "MIA_RED": "Miami (Ohio)",    # RedHawks      (confirmed: player roster)
    "NIU_HUS": "Northern Illinois",# Huskies
    "TOL_ROC": "Toledo",          # Rockets
    "WMI_BRO": "Western Michigan",# Broncos

    # ══════════════════════════════════════════════════════════════════════
    # MISSOURI VALLEY
    # ══════════════════════════════════════════════════════════════════════
    "EVA_ACE": "Evansville",      # Purple Aces   (confirmed: pattern)
    "ILL_RED": "Illinois State",  # Redbirds  (verify)
    "IND_SYC": "Indiana State",   # Sycamores
    "MIS_VAL": "Missouri State",  # Bears     (verify)
    "SOU_ILL": "Southern Illinois",# Salukis

    # ══════════════════════════════════════════════════════════════════════
    # OHIO VALLEY
    # ══════════════════════════════════════════════════════════════════════
    "EIU_PAN": "Eastern Illinois",# Panthers      (confirmed: pattern)
    "MOR_EAG": "Morehead State",  # Eagles        (confirmed: player roster)
    "MUR_RAC": "Murray State",    # Racers
    "SIU_SAL": "SIU Edwardsville",# Cougars   (verify)
    "TEN_TEC": "Tennessee Tech",  # Golden Eagles

    # ══════════════════════════════════════════════════════════════════════
    # HORIZON LEAGUE
    # ══════════════════════════════════════════════════════════════════════
    "ILL_TEC": "Illinois Tech",   # Scarlet Hawks (verify)
    "MIL_UNI": "Milwaukee",       # Panthers  (verify)
    "OHI_BOB": "Ohio",            # Bobcats
    "PUR_FOR": "Purdue Fort Wayne",# Mastodons
    "WRI_RAI": "Wright State",    # Raiders       (confirmed: pattern)
    "YSU_PEN": "Youngstown State",# Penguins

    # ══════════════════════════════════════════════════════════════════════
    # PATRIOT LEAGUE
    # ══════════════════════════════════════════════════════════════════════
    "ARM_BLA": "Army",            # Black Knights (confirmed: pattern)
    "BUC_BIS": "Bucknell",        # Bison
    "LAF_LEP": "Lafayette",       # Leopards
    "LEH_MOU": "Lehigh",          # Mountain Hawks
    "NAV_MID": "Navy",            # Midshipmen

    # ══════════════════════════════════════════════════════════════════════
    # IVY LEAGUE
    # ══════════════════════════════════════════════════════════════════════
    "BRO_BEA": "Brown",           # Bears
    "COL_LIO": "Columbia",        # Lions
    "DAR_GRE": "Dartmouth",       # Big Green
    "HAR_CRI": "Harvard",         # Crimson
    "PEN_QUA": "Penn",            # Quakers
    "PRI_TIG": "Princeton",       # Tigers
    "YAL_BUL": "Yale",            # Bulldogs

    # ══════════════════════════════════════════════════════════════════════
    # NEC (Northeast Conference)
    # ══════════════════════════════════════════════════════════════════════
    "FDU_KNI": "Fairleigh Dickinson",# Knights
    "LON_ISL22": "LIU",           # Sharks
    "NEW_HAV": "New Haven",       # Chargers      (confirmed: player roster — D1 2026)
    "WAG_SEA": "Wagner",          # Seahawks

    # ══════════════════════════════════════════════════════════════════════
    # SUMMIT LEAGUE
    # ══════════════════════════════════════════════════════════════════════
    "NOR_BIS": "North Dakota State",# Bison
    "SOU_JAC": "South Dakota State",# Jackrabbits (confirmed: player roster)
    "UNO_MAV": "Nebraska-Omaha",  # Mavericks

    # ══════════════════════════════════════════════════════════════════════
    # WAC (Western Athletic)
    # ══════════════════════════════════════════════════════════════════════
    "CAL_LAN": "Cal Baptist",     # Lancers
    "NEV_WOL": "Nevada",          # Wolf Pack
    "SAC_HOR": "Sacramento State",# Hornets
    "UTA_WOL": "Utah Valley",     # Wolverines

    # ══════════════════════════════════════════════════════════════════════
    # SOUTHERN CONFERENCE
    # ══════════════════════════════════════════════════════════════════════
    "WOF_TER": "Wofford",         # Terriers      (confirmed: pattern)
    "MER_BEA": "Mercer",          # Bears
    "WES_CAR": "Western Carolina",# Catamounts (verify — could be NOR_CAT)

    # ══════════════════════════════════════════════════════════════════════
    # SOUTHLAND
    # ══════════════════════════════════════════════════════════════════════
    "LAM_CAR": "Lamar",           # Cardinals
    "NOR_TEX": "North Texas",     # Mean Green (verify)
    "SAM_BEA": "Sam Houston",     # Bearkats  (verify)
    "STE_LUM": "Stephen F. Austin",# Lumberjacks

    # ══════════════════════════════════════════════════════════════════════
    # SWAC
    # ══════════════════════════════════════════════════════════════════════
    "JAC_GAM": "Jackson State",   # Tigers
    "SOU_JAG": "Southern",        # Jaguars

    # ══════════════════════════════════════════════════════════════════════
}


def get_team_name(code: str) -> str:
    """Return the school name for a TrackMan team code, or the code itself if unknown."""
    return TEAM_NAMES.get(code, code)


def normalize_teams(series):
    """
    Map a pandas Series of TrackMan team codes to school names.
    Unknown codes are left as-is so nothing breaks.

    Example:
        df["BatterTeam"] = normalize_teams(df["BatterTeam"])
        df["PitcherTeam"] = normalize_teams(df["PitcherTeam"])
    """
    return series.map(lambda c: TEAM_NAMES.get(c, c))
