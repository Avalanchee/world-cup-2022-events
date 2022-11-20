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

	# Environment Variables

	# Global Variables

	try:
		dHeaders = {"x-account-key": "2fy22ueTc"}
		sessionWorldCup = requests.Session()

		with open("worldcup.dat", "r") as fInput:
			dWorldCup = json.load(fInput, encoding="utf-8")

		while True:
			aEvents = []
			iTimestamp = calendar.timegm(datetime.datetime.now().timetuple())

			logWorldCup.debug("Requesting data - {0}".format(iTimestamp))
			try:
				httpResponse = sessionWorldCup.get("https://ipbc-web-fwc2022-sdk.akamaized.net/api/hbs/fwc/2022/matches", headers=dHeaders)
				dResponseMatches = httpResponse.json()

				for dMatch in dResponseMatches["matches"]:
					sMatchID = str(dMatch["matchId"])
					iMatchStatus = dMatch["status"]

					if sMatchID not in dWorldCup:
						dWorldCup[sMatchID] = {"status": iMatchStatus, "markers": []}
					iMatchStatusOld = dWorldCup[sMatchID]["status"]

					if iMatchStatus == 0:
						if iMatchStatusOld != 0:
							dEventText = {
								"round": "Round" if "roundName" not in dMatch else dMatch["roundName"],
								"group": "" if "groupName" not in dMatch or dMatch["groupName"] is None else " ({0})".format(dMatch["groupName"]),
								"home": "Home Team" if "teamNameLong" not in dMatch["homeTeam"] else dMatch["homeTeam"]["teamNameLong"],
								"away": "Away Team" if "teamNameLong" not in dMatch["awayTeam"] else dMatch["awayTeam"]["teamNameLong"],
								"home_score": "Home Score" if "scoreHome" not in dMatch["results"] else dMatch["results"]["scoreHome"],
								"away_score": "Away Score" if "scoreAway" not in dMatch["results"] else dMatch["results"]["scoreAway"],
							}
							aEvents.append("{round}{group} match has finished! {home} {home_score} - {away_score} {away}".format(**dEventText))
					elif iMatchStatus == 1:
						pass # Future match
					else:
						if iMatchStatusOld == 1:
							dEventText = {
								"round": "Round" if "roundName" not in dMatch else dMatch["roundName"],
								"group": "" if "groupName" not in dMatch or dMatch["groupName"] is None else " ({0})".format(dMatch["groupName"]),
								"home": "Home Team" if "teamNameLong" not in dMatch["homeTeam"] else dMatch["homeTeam"]["teamNameLong"],
								"away": "Away Team" if "teamNameLong" not in dMatch["awayTeam"] else dMatch["awayTeam"]["teamNameLong"],
								"degree": "??" if "temperature" not in dMatch["weatherConditions"] else dMatch["weatherConditions"]["temperature"],
								"humidity": "??" if "humidity" not in dMatch["weatherConditions"] else dMatch["weatherConditions"]["humidity"],
								"wind": "??" if "windSpeed" not in dMatch["weatherConditions"] else dMatch["weatherConditions"]["windSpeed"],
								"weather": "Weather" if "name" not in dMatch["weatherConditions"] else dMatch["weatherConditions"]["name"],
								"stadium": "Stadium" if "stadium" not in dMatch["stadium"] else dMatch["stadium"]["stadium"],
								"city": "City" if "city" not in dMatch["stadium"] else dMatch["stadium"]["city"]
							}
							aEvents.append("{round}{group} match between {home} and {away} is starting! It's a {weather} with {degree}c, {humidity}% humidity and {wind}km/h winds at {stadium} in {city}".format(**dEventText))

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
									"home_score": "?" if "score" not in dMarker["score"]["homeTeam"] else dMarker["score"]["homeTeam"]["score"],
									"away_score": "?" if "score" not in dMarker["score"]["awayTeam"] else dMarker["score"]["awayTeam"]["score"],
									"minute": "?" if "inGameTime" not in dMarker else dMarker["inGameTime"] // 60,
									"referee": "Referee" if "referees" not in dMatch else "Referee {0}".format([x["popularName"] for x in dMatch["referees"] if x["role"] == "REF"][0])
								}

								sEventText = dEventText["description"]

								if dEventText["description"] == "Toss coin":
									sEventText = "{home_country} {home_score} - {away_score} {away_country} [\"{minute}] - {referee} tosses the coin".format(**dEventText)
								if dEventText["description"] == "1st half":
									sEventText = "{home_country} {home_score} - {away_score} {away_country} [\"{minute}] - 1st half is starting".format(**dEventText)
								if dEventText["description"] == "First period extra time":
									sEventText = "{home_country} {home_score} - {away_score} {away_country} [\"{minute}] - First period extra time declared".format(**dEventText)
								if dEventText["description"] == "Half time":
									sEventText = "{home_country} {home_score} - {away_score} {away_country} [\"{minute}] - It is half time".format(**dEventText)
								if dEventText["description"] == "Second half":
									sEventText = "{home_country} {home_score} - {away_score} {away_country} [\"{minute}] - 2nd half is starting".format(**dEventText)
								if dEventText["description"] == "Second period extra time":
									sEventText = "{home_country} {home_score} - {away_score} {away_country} [\"{minute}] - Second period extra time declared".format(**dEventText)
								if dEventText["description"] in ["Goal canceled by VAR", "Card canceled by VAR", "Penalty Canceled by VAR"]:
									sEventText = "{home_country} {home_score} - {away_score} {away_country} [\"{minute}] - {description}!".format(**dEventText)
								if dEventText["description"] in ["Goal", "Own goal", "Yellow card", "Red card", "Goalkeeper Change"]:
									dEventText["player"] = "Player" if "playerName" not in dMarker else dMarker["playerName"]
									dEventText["player_country"] = "Team"

									if dMarker["challengerId"] == dMarker["score"]["homeTeam"]["id"]:
										dEventText["player_country"] = dMarker["score"]["homeTeam"]["teamNameLong"]
									elif dMarker["challengerId"] == dMarker["score"]["awayTeam"]["id"]:
										dEventText["player_country"] = dMarker["score"]["awayTeam"]["teamNameLong"]

									if dEventText["description"] == "Goal":
										sEventText = "{home_country} {home_score} - {away_score} {away_country} [\"{minute}] - Goal! {player} scores for {player_country}!".format(**dEventText)
									if dEventText["description"] == "Own goal":
										sEventText = "{home_country} {home_score} - {away_score} {away_country} [\"{minute}] - Oh no! Own goal! {player} scores for {player_country}!".format(**dEventText)
									if dEventText["description"] == "Yellow card":
										sEventText = "{home_country} {home_score} - {away_score} {away_country} [\"{minute}] - Yellow card for {player} from {player_country}!".format(**dEventText)
									if dEventText["description"] == "Red card":
										sEventText = "{home_country} {home_score} - {away_score} {away_country} [\"{minute}] - Red card for {player} from {player_country}!".format(**dEventText)
									if dEventText["description"] == "Goalkeeper Change":
										sEventText = "{home_country} {home_score} - {away_score} {away_country} [\"{minute}] - Goalkeeper change for {player_country}!".format(**dEventText)

								if sEventText != dEventText["description"]:
									aEvents.append(sEventText)

								dWorldCup[sMatchID]["markers"].append({"id": sMarkerID, "text": sEventText})
						if aEvents != []:
							with open(os.path.join("debug", "{0}-player-{1}.json".format(iTimestamp, sMatchID)), "w") as fOutput:
								json.dump(dResponsePlayer, fOutput, indent=4)

					dWorldCup[sMatchID]["status"] = iMatchStatus

				temp_bot.Say(aEvents, "WorldCup", apArguments.debug, apArguments.debug, logWorldCup)

				if aEvents != []:
					with open(os.path.join("debug", "{0}-matches.json".format(iTimestamp)), "w") as fOutput:
						json.dump(dResponseMatches, fOutput, indent=4)

				with open("worldcup.dat", "w") as fOutput:
					json.dump(dWorldCup, fOutput, indent=4)
			except:
				logWorldCup.exception("Request failed!")

			time.sleep(10)
	except:
		logWorldCup.exception("Program Exception!")