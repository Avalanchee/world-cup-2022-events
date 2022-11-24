#!/usr/bin/python
# coding=utf-8
import os
import sys
import time
import json
import copy
import logging
import datetime
import requests
import calendar
import argparse
import temp_bot

if __name__ == "__main__":
	# Argument Parser
	apParser = argparse.ArgumentParser()
	apParser.add_argument("--debug", action='store_true', help="Debug mode")
	apParser.add_argument("--mode", nargs="+", help="mode1/mode2")
	apArguments = apParser.parse_args()

	class Formatter(logging.Formatter):
		def __init__(self, f, ft, exc):
			self.formatter = logging.Formatter(f, ft)
			self.exc = exc

		def format(self, record):
			new_record = copy.copy(record)
			if not self.exc:
				new_record.exc_info = ()
			return self.formatter.format(new_record)

	# Logger
	logWorldCup = logging.getLogger("WorldCup")
	logWorldCup.setLevel(logging.DEBUG)
	logFormat = Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s", "%Y-%m-%d %H:%M:%S", False)
	logFormatFull = Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s", "%Y-%m-%d %H:%M:%S", True)
	logHandlerFile = logging.FileHandler("worldcup.log", encoding="utf=8")
	logHandlerFileError = logging.FileHandler("worldcup.err.log", encoding="utf=8")
	logHandlerStream = logging.StreamHandler(sys.stdout)
	logHandlerFile.setLevel(logging.DEBUG if apArguments.debug else logging.INFO)
	logHandlerFile.setFormatter(logFormat)
	logHandlerFileError.setLevel(logging.ERROR)
	logHandlerFileError.setFormatter(logFormatFull)
	logHandlerStream.setLevel(logging.DEBUG if apArguments.debug else logging.INFO)
	logHandlerStream.setFormatter(logFormatFull)
	logWorldCup.addHandler(logHandlerFile)
	logWorldCup.addHandler(logHandlerFileError)
	logWorldCup.addHandler(logHandlerStream)

	# Defines
	dCountryFlags = {
		"ARG": "\U0001f1e6\U0001f1f7",
		"AUS": "\U0001f1e6\U0001f1fa",
		"BEL": "\U0001f1e7\U0001f1ea",
		"BRA": "\U0001f1e7\U0001f1f7",
		"CAN": "\U0001f1e8\U0001f1e6",
		"CMR": "\U0001f1e8\U0001f1f2",
		"CRC": "\U0001f1e8\U0001f1f7",
		"CRO": "\U0001f1ed\U0001f1f7",
		"DEN": "\U0001f1e9\U0001f1f0",
		"ECU": "\U0001f1ea\U0001f1e8",
		"ENG": "\U0001f3f4\U000e0067\U000e0062\U000e0065\U000e006e\U000e0067\U000e007f",
		"ESP": "\U0001f1ea\U0001f1f8",
		"FRA": "\U0001f1eb\U0001f1f7",
		"GER": "\U0001f1e9\U0001f1ea",
		"GHA": "\U0001f1ec\U0001f1ed",
		"IRN": "\U0001f1ee\U0001f1f7",
		"JPN": "\U0001f1ef\U0001f1f5",
		"KOR": "\U0001f1f0\U0001f1f7",
		"KSA": "\U0001f1f8\U0001f1e6",
		"MAR": "\U0001f1f2\U0001f1e6",
		"MEX": "\U0001f1f2\U0001f1fd",
		"NED": "\U0001f1f3\U0001f1f1",
		"POL": "\U0001f1f5\U0001f1f1",
		"POR": "\U0001f1f5\U0001f1f9",
		"QAT": "\U0001f1f6\U0001f1e6",
		"SEN": "\U0001f1f8\U0001f1f3",
		"SRB": "\U0001f1f7\U0001f1f8",
		"SUI": "\U0001f1e8\U0001f1ed",
		"TUN": "\U0001f1f9\U0001f1f3",
		"URU": "\U0001f1fa\U0001f1fe",
		"USA": "\U0001f1fa\U0001f1f8",
		"WAL": "\U0001f3f4\U000e0067\U000e0062\U000e0077\U000e006c\U000e0073\U000e007f"
	}
	# Environment Variables

	# Global Variables
	iPreMatchTimeSeconds = 300
	iPostMatchGraceSeconds = 180
	iSleepTimeSeconds = 6

	try:
		dHeaders = {"x-account-key": "2fy22ueTc"}
		sessionWorldCup = requests.Session()

		with open("worldcup.dat", "r") as fInput:
			dWorldCup = json.load(fInput, encoding="utf-8")

		while True:
			aEvents = []
			iTimestamp = calendar.timegm(datetime.datetime.now().timetuple())
			dateUTC = datetime.datetime.utcnow()

			logWorldCup.debug("Requesting data - {0}".format(iTimestamp))
			try:
				httpResponse = sessionWorldCup.get("https://ipbc-web-fwc2022-sdk.akamaized.net/api/hbs/fwc/2022/matches", headers=dHeaders)
				dResponseMatches = httpResponse.json()

				for dMatch in dResponseMatches["matches"]:
					sMatchID = str(dMatch["matchId"])
					iMatchStatus = dMatch["status"]
					dateStartTime = datetime.datetime.strptime(dMatch["dateUtc"], "%Y-%m-%dT%H:%M:%S")

					if sMatchID not in dWorldCup:
						dWorldCup[sMatchID] = {"status": None, "markers": [], "finished": 0, "injury": {}, "pre_match": False}

					if iMatchStatus == 0 and dWorldCup[sMatchID]["status"] is not None and dWorldCup[sMatchID]["status"] > 0:
						dEventText = {
							"round": "Round" if "roundName" not in dMatch else dMatch["roundName"],
							"group": "" if "groupName" not in dMatch or dMatch["groupName"] is None else " ({0})".format(dMatch["groupName"]),
							"home": "Home Team" if "teamNameLong" not in dMatch["homeTeam"] else dMatch["homeTeam"]["teamNameLong"],
							"away": "Away Team" if "teamNameLong" not in dMatch["awayTeam"] else dMatch["awayTeam"]["teamNameLong"],
							"home_score": "Home Score" if "scoreHome" not in dMatch["results"] else dMatch["results"]["scoreHome"],
							"away_score": "Away Score" if "scoreAway" not in dMatch["results"] else dMatch["results"]["scoreAway"],
							"home_penalty_score": 0 if "penaltyScoreHome" not in dMatch["results"] else dMatch["results"]["penaltyScoreHome"],
							"away_penalty_score": 0 if "penaltyScoreAway" not in dMatch["results"] else dMatch["results"]["penaltyScoreAway"],
							"attendance": 0 if "attendance" not in dMatch or dMatch["attendance"] is None else dMatch["attendance"],
							"stadium": "Stadium" if "stadium" not in dMatch["stadium"] else dMatch["stadium"]["stadium"],
						}

						dEventText["winner"] = "Winner"
						dEventText["loser"] = "Loser"
						if dMatch["results"]["winnerTeamId"] == dMatch["homeTeam"]["teamId"]:
							dEventText["winner"] = dMatch["homeTeam"]["teamNameLong"]
							dEventText["loser"] = dMatch["awayTeam"]["teamNameLong"]
						elif dMatch["results"]["winnerTeamId"] == dMatch["awayTeam"]["teamId"]:
							dEventText["winner"] = dMatch["awayTeam"]["teamNameLong"]
							dEventText["loser"] = dMatch["homeTeam"]["teamNameLong"]

						if dEventText["winner"] == "Winner" or dEventText["loser"] == "Loser":
							sEventText = "{round}{group} match has finished! Final score: {home} {home_score} - {away_score} {away}".format(**dEventText)
						else:
							sEventText = "{winner} has won {round}{group} match against {loser}! Final score: {home} {home_score} - {away_score} {away}".format(**dEventText)
						if dEventText["home_penalty_score"] > 0 or dEventText["away_penalty_score"] > 0:
							sEventText += " ({home_penalty_score} - {away_penalty_score} after penalties)".format(**dEventText)

						aEvents.append(sEventText)

						if dEventText["attendance"] > 0:
							aEvents.append("{attendance:,} spectators were in {stadium}".format(**dEventText))

						dWorldCup[sMatchID]["finished"] = iTimestamp
					elif iMatchStatus == 1:
						dEventText = {
							"round": "Round" if "roundName" not in dMatch else dMatch["roundName"],
							"group": "" if "groupName" not in dMatch or dMatch["groupName"] is None else " ({0})".format(dMatch["groupName"]),
							"home": "Home Team" if dMatch["homeTeam"] is None or "teamNameLong" not in dMatch["homeTeam"] else dMatch["homeTeam"]["teamNameLong"],
							"away": "Away Team" if dMatch["awayTeam"] is None or "teamNameLong" not in dMatch["awayTeam"] else dMatch["awayTeam"]["teamNameLong"],
							"degree": "??" if "temperature" not in dMatch["weatherConditions"] else dMatch["weatherConditions"]["temperature"],
							"humidity": "??" if "humidity" not in dMatch["weatherConditions"] else dMatch["weatherConditions"]["humidity"],
							"wind": "??" if "windSpeed" not in dMatch["weatherConditions"] else dMatch["weatherConditions"]["windSpeed"],
							"weather": "Weather" if "name" not in dMatch["weatherConditions"] else dMatch["weatherConditions"]["name"],
							"match_number": "?" if "matchNumber" not in dMatch else dMatch["matchNumber"],
							"stadium": "Stadium" if "stadium" not in dMatch["stadium"] else dMatch["stadium"]["stadium"],
							"city": "City" if "city" not in dMatch["stadium"] else dMatch["stadium"]["city"],
							"pre_match_time": round((dateStartTime - dateUTC).total_seconds() / 60)
						}

						if dWorldCup[sMatchID]["status"] == 1 and not dWorldCup[sMatchID]["pre_match"] and 0 < (dateStartTime - dateUTC).total_seconds() < iPreMatchTimeSeconds:
							aEvents.append("{round}{group} match #{match_number} between {home} and {away} is starting in {pre_match_time} minutes! Weather is {weather} with {degree}c, {humidity}% humidity and {wind}km/h winds at {stadium} in {city}".format(**dEventText))
							dWorldCup[sMatchID]["pre_match"] = True

					elif iMatchStatus > 1 or (iMatchStatus == 0 and iTimestamp - dWorldCup[sMatchID]["finished"] < iPostMatchGraceSeconds):
						logWorldCup.debug("Match {0} in progress".format(sMatchID))
						dEventText = {
							"round": "Round" if "roundName" not in dMatch else dMatch["roundName"],
							"group": "" if "groupName" not in dMatch or dMatch["groupName"] is None else " ({0})".format(dMatch["groupName"]),
							"home": "Home Team" if dMatch["homeTeam"] is None or "teamNameLong" not in dMatch["homeTeam"] else dMatch["homeTeam"]["teamNameLong"],
							"away": "Away Team" if dMatch["awayTeam"] is None or "teamNameLong" not in dMatch["awayTeam"] else dMatch["awayTeam"]["teamNameLong"],
							"degree": "??" if "temperature" not in dMatch["weatherConditions"] else dMatch["weatherConditions"]["temperature"],
							"humidity": "??" if "humidity" not in dMatch["weatherConditions"] else dMatch["weatherConditions"]["humidity"],
							"wind": "??" if "windSpeed" not in dMatch["weatherConditions"] else dMatch["weatherConditions"]["windSpeed"],
							"weather": "Weather" if "name" not in dMatch["weatherConditions"] else dMatch["weatherConditions"]["name"],
							"match_number": "?" if "matchNumber" not in dMatch else dMatch["matchNumber"],
							"stadium": "Stadium" if "stadium" not in dMatch["stadium"] else dMatch["stadium"]["stadium"],
							"city": "City" if "city" not in dMatch["stadium"] else dMatch["stadium"]["city"]
						}

						for dInjuryTime in dMatch["injuryTimes"]:
							sInjuryTimePhase = str(dInjuryTime["phaseId"])
							if sInjuryTimePhase not in dWorldCup[sMatchID]["injury"]:
								if sInjuryTimePhase == "1":
									dEventText["phase"] = "1st half"
								if sInjuryTimePhase == "2":
									dEventText["phase"] = "2nd half"
								if sInjuryTimePhase == "3":
									dEventText["phase"] = "3rd phase"
								if sInjuryTimePhase == "4":
									dEventText["phase"] = "4th phase"
								dEventText["injury_time"] = dInjuryTime["value"]

								aEvents.append("{home} vs. {away} - {injury_time} minutes extra time for {phase}".format(**dEventText))
								dWorldCup[sMatchID]["injury"][sInjuryTimePhase] = dInjuryTime["value"]

						httpResponse = sessionWorldCup.get("https://ipbc-web-fwc2022-sdk.akamaized.net/api/hbs/fwc/2022/players/{0}/player".format(sMatchID), headers=dHeaders)
						dResponsePlayer = httpResponse.json()
						aMarkers = sorted(dResponsePlayer["markers"], key=lambda x: x["startTime"])
						for dMarker in aMarkers:
							sMarkerID = str(dMarker["id"])
							if sMarkerID not in [x["id"] for x in dWorldCup[sMatchID]["markers"]]:
								dEventText = {
									"description": "" if "description" not in dMarker else dMarker["description"],
									"home": "Home Team" if "teamNameLong" not in dMarker["score"]["homeTeam"] else dMarker["score"]["homeTeam"]["teamNameLong"],
									"away": "Away Team" if "teamNameLong" not in dMarker["score"]["awayTeam"] else dMarker["score"]["awayTeam"]["teamNameLong"],
									"home_country": "???" if "teamCountryCode" not in dMatch["homeTeam"] else dMatch["homeTeam"]["teamCountryCode"],
									"away_country": "???" if "teamCountryCode" not in dMatch["awayTeam"] else dMatch["awayTeam"]["teamCountryCode"],
									"home_flag": "" if "teamCountryCode" not in dMatch["homeTeam"] or dMatch["homeTeam"]["teamCountryCode"] not in dCountryFlags else dCountryFlags[dMatch["homeTeam"]["teamCountryCode"]],
									"away_flag": "" if "teamCountryCode" not in dMatch["awayTeam"] or dMatch["awayTeam"]["teamCountryCode"] not in dCountryFlags else dCountryFlags[dMatch["awayTeam"]["teamCountryCode"]],
									"home_score": "?" if "score" not in dMarker["score"]["homeTeam"] else dMarker["score"]["homeTeam"]["score"],
									"away_score": "?" if "score" not in dMarker["score"]["awayTeam"] else dMarker["score"]["awayTeam"]["score"],
									"home_penalty_score": "" if "penaltyScore" not in dMarker["score"]["homeTeam"] or dMarker["score"]["homeTeam"]["penaltyScore"] == 0 else "(+{0})".format(dMarker["score"]["homeTeam"]["penaltyScore"]),
									"away_penalty_score": "" if "penaltyScore" not in dMarker["score"]["awayTeam"] or dMarker["score"]["awayTeam"]["penaltyScore"] == 0 else "(+{0})".format(dMarker["score"]["awayTeam"]["penaltyScore"]),
									"match_start": 0 if "streams" not in dResponsePlayer else dResponsePlayer["streams"]["broadcasts"][0]["officialMatchStart"],
									"real_match_start": 0 if "streams" not in dResponsePlayer else dResponsePlayer["streams"]["broadcasts"][0]["realMatchStart"],
									"minute": "?" if "inGameTime" not in dMarker else dMarker["inGameTime"] // 60,
									"injury_minute": "" if "injuryMinute" not in dMatch or dMatch["injuryMinute"] is None or dMatch["injuryMinute"] == 0 else "+{0}\u2032".format(dMatch["injuryMinute"]),
									"referee": "Referee" if "referees" not in dMatch else "Referee {0}".format([x["popularName"] for x in dMatch["referees"] if x["role"] == "REF"][0]),
								}

								sEventText = dEventText["description"]
								sEventTextPrefix = "{home_country} {home_flag} {home_score}{home_penalty_score} - {away_score}{away_penalty_score} {away_flag} {away_country} [{minute}\u2032{injury_minute}]".format(**dEventText)

								if dEventText["description"] == "Toss coin":
									sEventText = sEventTextPrefix + " - {referee} tosses the coin".format(**dEventText)
								if dEventText["description"] == "1st half":
									dEventText["start_offset"] = ". Match started {0} seconds after official time".format(dEventText["real_match_start"] - dEventText["match_start"]) if dEventText["real_match_start"] - dEventText["match_start"] > 0 else ""
									sEventText = sEventTextPrefix + " - 1st half is starting{start_offset}".format(**dEventText)
								if dEventText["description"] == "First period extra time":
									sEventText = sEventTextPrefix + " - First period extra time declared".format(**dEventText)
								if dEventText["description"] == "Half time":
									sEventText = sEventTextPrefix + " - Half time break".format(**dEventText)
								if dEventText["description"] == "Second half":
									sEventText = sEventTextPrefix + " - 2nd half is starting".format(**dEventText)
								if dEventText["description"] == "Second period extra time":
									sEventText = sEventTextPrefix + " - Second period extra time declared".format(**dEventText)
								if dEventText["description"] in ["Goal canceled by VAR", "Card canceled by VAR", "Penalty Canceled by VAR"]:
									sEventText = sEventTextPrefix + " - {description}!".format(**dEventText)
								if dEventText["description"] in ["Goal", "Own goal", "Yellow card", "Red card", "Penalty", "Goalkeeper Change"]:
									dEventText["player"] = "Player" if "playerName" not in dMarker else dMarker["playerName"]
									dEventText["player_country"] = "Team"

									if dMarker["challengerId"] == dMarker["score"]["homeTeam"]["id"]:
										dEventText["player_country"] = dMarker["score"]["homeTeam"]["teamNameLong"]
									elif dMarker["challengerId"] == dMarker["score"]["awayTeam"]["id"]:
										dEventText["player_country"] = dMarker["score"]["awayTeam"]["teamNameLong"]

									if dEventText["description"] == "Goal":
										sEventText = sEventTextPrefix + " - Goal! {player} scores for {player_country}!".format(**dEventText)
									if dEventText["description"] == "Own goal":
										sEventText = sEventTextPrefix + " - Oh no! Own goal! {player} scores for {player_country}!".format(**dEventText)
									if dEventText["description"] == "Penalty":
										sEventText = sEventTextPrefix + " - Penalty kick for {player_country}! {player} will take the shot".format(**dEventText)
									if dEventText["description"] == "Yellow card":
										sEventText = sEventTextPrefix + " - Yellow card for {player} from {player_country}!".format(**dEventText)
									if dEventText["description"] == "Red card":
										sEventText = sEventTextPrefix + " - Red card for {player} from {player_country}!".format(**dEventText)
									if dEventText["description"] == "Goalkeeper Change":
										sEventText = sEventTextPrefix + " - Goalkeeper change for {player_country}!".format(**dEventText)

								if sEventText != dEventText["description"]:
									aEvents.append(sEventText)

								dWorldCup[sMatchID]["markers"].append({"id": sMarkerID, "text": sEventText})
						if aEvents != [] or apArguments.debug:
							with open(os.path.join("debug", "{0}-player-{1}.json".format(iTimestamp, sMatchID)), "w") as fOutput:
								json.dump(dResponsePlayer, fOutput, indent=4)

					dWorldCup[sMatchID]["status"] = iMatchStatus

				temp_bot.Say(aEvents, "WorldCup", apArguments.debug, apArguments.debug, logWorldCup)

				if aEvents != [] or apArguments.debug:
					with open(os.path.join("debug", "{0}-matches.json".format(iTimestamp)), "w") as fOutput:
						json.dump(dResponseMatches, fOutput, indent=4)

				with open("worldcup.dat", "w") as fOutput:
					json.dump(dWorldCup, fOutput, indent=4)
			except:
				logWorldCup.exception("Request failed!")

			time.sleep(iSleepTimeSeconds)
	except:
		logWorldCup.exception("Program Exception!")
