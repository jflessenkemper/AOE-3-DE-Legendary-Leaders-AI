//==============================================================================
/* aiLoaderStandard.xs
   
   Create a new loader file for each personality.  Always specify loader
   file names (not the main or header files) in scenarios.
*/
//==============================================================================



include "aiHeader.xs";     // Gets global vars, function forward declarations
include "aiMain.xs";       // The bulk of the AI
include "leaders\leaderCommon.xs";
include "leaders\leader_revolution_support.xs";
include "leaders\leader_revolution_commanders.xs";
include "leaders\leader_bourbon.xs";
include "leaders\leader_napoleon.xs";
include "leaders\leader_wellington.xs";
include "leaders\leader_frederick.xs";
include "leaders\leader_catherine.xs";
include "leaders\leader_isabella.xs";
include "leaders\leader_suleiman.xs";
include "leaders\leader_henry.xs";
include "leaders\leader_maurice.xs";
include "leaders\leader_washington.xs";
include "leaders\leader_hidalgo.xs";
include "leaders\leader_garibaldi.xs";
include "leaders\leader_valette.xs";
include "leaders\leader_montezuma.xs";
include "leaders\leader_kangxi.xs";
include "leaders\leader_menelik.xs";
include "leaders\leader_hiawatha.xs";
include "leaders\leader_usman.xs";
include "leaders\leader_pachacuti.xs";
include "leaders\leader_shivaji.xs";
include "leaders\leader_tokugawa.xs";
include "leaders\leader_crazy_horse.xs";
include "leaders\leader_gustavus.xs";



//==============================================================================
/*	preInit()

	This function is called in main() before any of the normal initialization 
	happens.  Use it to override default values of variables as needed for 
	personality or scenario effects.
*/
//==============================================================================
void preInit(void)
{
   llVerboseEcho("preInit() starting.");

   string legendaryLeaderCivName = kbGetCivName(cMyCiv);

   initLegendaryRevolutionSupport();

   if (cMyCiv == cCivFrench)
   {
      initLeaderBourbon();
   }
   else if (legendaryLeaderCivName == "RvltModNapoleonicFrance")
   {
      initLeaderNapoleon();
   }
   else if (cMyCiv == cCivBritish)
   {
      initLeaderWellington();
   }
   else if (cMyCiv == cCivGermans)
   {
      initLeaderFrederick();
   }
   else if (cMyCiv == cCivRussians)
   {
      initLeaderCatherine();
   }
   else if (cMyCiv == cCivSpanish)
   {
      initLeaderIsabella();
   }
   else if (cMyCiv == cCivOttomans)
   {
      initLeaderSuleiman();
   }
   else if (cMyCiv == cCivPortuguese)
   {
      initLeaderHenry();
   }
   else if (cMyCiv == cCivDutch)
   {
      initLeaderMaurice();
   }
   else if (cMyCiv == cCivDEAmericans)
   {
      initLeaderWashington();
   }
   else if (cMyCiv == cCivDEMexicans)
   {
      initLeaderHidalgo();
   }
   else if (cMyCiv == cCivDEItalians)
   {
      initLeaderGaribaldi();
   }
   else if (cMyCiv == cCivDEMaltese)
   {
      initLeaderValette();
   }
   else if (cMyCiv == cCivXPAztec)
   {
      initLeaderMontezuma();
   }
   else if (cMyCiv == cCivChinese)
   {
      initLeaderKangxi();
   }
   else if (cMyCiv == cCivDEEthiopians)
   {
      initLeaderMenelik();
   }
   else if (cMyCiv == cCivXPIroquois)
   {
      initLeaderHiawatha();
   }
   else if (cMyCiv == cCivDEHausa)
   {
      initLeaderUsman();
   }
   else if (cMyCiv == cCivDEInca)
   {
      initLeaderPachacuti();
   }
   else if (cMyCiv == cCivIndians)
   {
      initLeaderShivaji();
   }
   else if (cMyCiv == cCivJapanese)
   {
      initLeaderTokugawa();
   }
   else if (cMyCiv == cCivXPSioux)
   {
      initLeaderCrazyHorse();
   }
   else if (cMyCiv == cCivDESwedish)
   {
      initLeaderGustavus();
   }
   else if (civIsRevolution() == true)
   {
      initLegendaryRevolutionCommander();
   }

   llAssignLeaderIdentity();
   llApplyBuildStyleForActiveCiv();

   if (aiGetGameMode() == cGameModeEconomyMode)
   {
      llVerboseEcho("Economy mode setup");

      btRushBoom = -1.0; // boom
      btOffenseDefense = -1.0; // defend
      cvOkToAttack = false;
      cvOkToTrainArmy = false;
      cvOkToTrainNavy = false;
      cvOkToAllyNatives = false;
   }
}




//==============================================================================
/*	postInit()

	This function is called in main() after the normal initialization is 
	complete.  Use it to override settings and decisions made by the startup logic.
*/
//==============================================================================
void postInit(void)
{
   llVerboseEcho("postInit() starting.");

   // Per-nation walling: enable the Age-1 ring-wall rule for every leader.
   // The rule itself checks llShouldBuildLegendaryWalls(true) which respects
   // gLLEarlyWallingEnabled and gLLWallLevel per leader — aggressive styles
   // (SteppeCavalryWedge / MobileFrontierScatter / JungleGuerrillaNetwork)
   // opt out via earlyWalls=false in their style helpers, so the rule
   // effectively no-ops for them. Defensive leaders (Wellington, Valette,
   // Pachacuti, Frederick) get an early ring-wall around the TC.
   xsEnableRule("explorationAgeWalling");

   if (cLLReplayProbes == true)
   {
      xsEnableRule("llHeartbeat");
      xsEnableRule("llPlanSnapshot");
   }

   enableLegendaryRevolutionSupportRules();
   enableLegendaryRevolutionCommanderRules();
   enableLeaderBourbonRules();
   enableLeaderNapoleonRules();
   enableLeaderWellingtonRules();
   enableLeaderFrederickRules();
   enableLeaderCatherineRules();
   enableLeaderIsabellaRules();
   enableLeaderSuleimanRules();
   enableLeaderHenryRules();
   enableLeaderMauriceRules();
   enableLeaderWashingtonRules();
   enableLeaderHidalgoRules();
   enableLeaderGaribaldiRules();
   enableLeaderValetteRules();
   enableLeaderMontezumaRules();
   enableLeaderKangxiRules();
   enableLeaderMenelikRules();
   enableLeaderHiawathaRules();
   enableLeaderUsmanRules();
   enableLeaderPachacutiRules();
   enableLeaderShivajiRules();
   enableLeaderTokugawaRules();
   enableLeaderCrazyHorseRules();
   enableLeaderGustavusRules();

   // ── LL-BOOT probe ───────────────────────────────────────────────────────
   // One-shot broadcast of this AI's identity so the replay parser records
   // leader/chatset/doctrine/wall-strategy wiring at t=0 for every AI in the
   // match. Catches Barbary-blank, Napoleon-wrong-name, wrong-chatset
   // regressions immediately without needing in-match screenshots.
   llProbe("meta.boot",
      "chatset=" + gLLChatsetKey +
      " wallStrategy=" + gLLWallStrategy +
      " buildStyle=" + llGetBuildStyleName(gLLBuildStyle) +
      " wallLevel=" + gLLWallLevel +
      " earlyWalls=" + gLLEarlyWallingEnabled +
      " rush=" + btRushBoom +
      " off=" + btOffenseDefense +
      " inf=" + btBiasInf +
      " cav=" + btBiasCav +
      " art=" + btBiasArt);

   // ── LL-SETUP probe ──────────────────────────────────────────────────────
   // Match-level context: game mode, difficulty, team, player count. Shared
   // context for every AI's probes so post-match analysis can normalise
   // across Supremacy/Deathmatch/Treaty/Empire-Wars runs.
   llProbe("meta.setup",
      "gameMode=" + aiGetGameMode() +
      " difficulty=" + cDifficultyCurrent +
      " team=" + kbGetPlayerTeam(cMyID) +
      " players=" + cNumberPlayers +
      " startAge=" + kbGetAge() +
      " okAttack=" + cvOkToAttack +
      " okTaunt=" + cvOkToTaunt);

   // ── LL-ECOSNAP probe ────────────────────────────────────────────────────
   // Initial economic state snapshot — DEFERRED: postInit runs before the
   // engine seeds starting resources/villagers, so an immediate snapshot
   // captures all-zero garbage (verified in replay). llInitialEconSnapshot
   // fires once after 5s when the starting bundle is populated.
   if (cLLReplayProbes == true)
   {
      xsEnableRule("llInitialEconSnapshot");
   }
}




//==============================================================================
/*	Rules

	Add personality-specific or scenario-specific rules in the section below.
*/
//==============================================================================

//==============================================================================
// llHeartbeat
// Periodic time-series probe. Emits age, resources, pop, army, score every
// 60s so replay analysis can chart economic/military trajectory without
// relying on spiky event-driven probes alone.
//==============================================================================
rule llHeartbeat
inactive
minInterval 60
{
   llProbe("telem.heartbeat",
      "age=" + kbGetAge() +
      " food=" + kbResourceGet(cResourceFood) +
      " wood=" + kbResourceGet(cResourceWood) +
      " gold=" + kbResourceGet(cResourceGold) +
      " pop=" + kbGetPop() +
      " vills=" + kbUnitCount(cMyID, gEconUnit, cUnitStateAlive) +
      " armyPop=" + aiGetMilitaryPop() +
      " score=" + aiGetScore(cMyID));
}

//==============================================================================
// llPlanSnapshot
// Phase-2 periodic snapshot of the AI's active plan inventory. Fires every
// 60s alongside the heartbeat. Three probes per tick:
//   * mil.plan_snap   — combat plan count (offense + defense)
//   * plan.build_snap — build plans (incl. wall plans), repair, gather
//   * navy.fleet_snap — naval unit and transport-plan inventory
// We use periodic snapshots rather than instrumenting all 91 aiPlanCreate
// call sites — equivalent ground truth, far less integration risk.
//==============================================================================
rule llPlanSnapshot
inactive
minInterval 60
{
   int combatPlans = aiPlanGetNumber(cPlanCombat, -1, true);
   int attackPlans = aiPlanGetNumber(cPlanAttack, -1, true);
   int defendPlans = aiPlanGetNumber(cPlanDefend, -1, true);
   int buildPlans = aiPlanGetNumber(cPlanBuild, -1, true);
   int wallPlans = aiPlanGetNumber(cPlanBuildWall, -1, true);
   int repairPlans = aiPlanGetNumber(cPlanRepair, -1, true);
   int gatherPlans = aiPlanGetNumber(cPlanGather, -1, true);
   int researchPlans = aiPlanGetNumber(cPlanResearch, -1, true);
   int transportPlans = aiPlanGetNumber(cPlanTransport, -1, true);
   int explorePlans = aiPlanGetNumber(cPlanExplore, -1, true);

   llProbe("mil.plan_snap",
      "combat=" + combatPlans +
      " attack=" + attackPlans +
      " defend=" + defendPlans +
      " explore=" + explorePlans +
      " militaryPop=" + aiGetMilitaryPop());

   llProbe("plan.build_snap",
      "build=" + buildPlans +
      " walls=" + wallPlans +
      " repair=" + repairPlans +
      " gather=" + gatherPlans +
      " research=" + researchPlans +
      " tcs=" + kbUnitCount(cMyID, gTownCenterUnit, cUnitStateABQ) +
      " houses=" + kbUnitCount(cMyID, gHouseUnit, cUnitStateABQ));

   llProbe("navy.fleet_snap",
      "transports=" + transportPlans +
      " warships=" + kbUnitCount(cMyID, cUnitTypeAbstractWarShip, cUnitStateAlive) +
      " fishing=" + kbUnitCount(cMyID, gFishingBoatUnit, cUnitStateAlive) +
      " docks=" + kbUnitCount(cMyID, gDockUnit, cUnitStateABQ));
}

//==============================================================================
// llInitialEconSnapshot
// Fires once after starting resources/villagers seed. Deferred from postInit
// because immediate emission captures zero-state garbage before the engine
// grants the starting bundle.
//==============================================================================
rule llInitialEconSnapshot
inactive
minInterval 5
{
   // Wait until either starting resources or starting villagers have been
   // granted — whichever comes first signals seeding is complete.
   if ((kbResourceGet(cResourceFood) <= 0.0) &&
       (kbUnitCount(cMyID, gEconUnit, cUnitStateAlive) <= 0))
   {
      return;
   }
   llProbe("econ.snap",
      "age=" + kbGetAge() +
      " food=" + kbResourceGet(cResourceFood) +
      " wood=" + kbResourceGet(cResourceWood) +
      " gold=" + kbResourceGet(cResourceGold) +
      " pop=" + kbGetPop() +
      " vills=" + kbUnitCount(cMyID, gEconUnit, cUnitStateAlive));
   xsDisableSelf();
}