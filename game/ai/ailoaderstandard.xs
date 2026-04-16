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
   aiEcho("preInit() starting.");

   string legendaryLeaderCivName = kbGetCivName(cMyCiv);

   initLegendaryRevolutionSupport();

   if ((cMyCiv == cCivFrench) || (legendaryLeaderCivName == "RvltModNapoleonicFrance"))
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

   if (aiGetGameMode() == cGameModeEconomyMode)
   {
      aiEcho("Economy mode setup");

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
   aiEcho("postInit() starting.");
   enableLegendaryRevolutionSupportRules();
   enableLegendaryRevolutionCommanderRules();
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
}




//==============================================================================
/*	Rules

	Add personality-specific or scenario-specific rules in the section below.
*/
//==============================================================================