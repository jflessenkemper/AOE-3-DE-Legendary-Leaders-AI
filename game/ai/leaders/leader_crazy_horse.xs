//==============================================================================
/* leader_crazy_horse.xs */
//==============================================================================

bool gCrazyHorseRulesEnabled = false;

void initLeaderCrazyHorse(void)
{
   llVerboseEcho("Legendary Leaders: activating Crazy Horse personality.");

   llSetAggressivePersonality();
   btRushBoom = 0.7;
   btOffenseDefense = 0.8;
   btBiasTrade = -0.4;
   btBiasNative = 0.5;
   llSetMilitaryFocus(0.2, 0.8, -0.1);
   llSetLeaderTacticalDoctrine(0.34, 0.86, -1, -3.0);
   cvMaxTowers = 1;
   llSetPrisonerDoctrine(cLLPrisonerDoctrineExecution, 0.40, 70.0);
   llEnablePrisonerSystem();
   gCrazyHorseRulesEnabled = true;
   llLogLeaderState("Crazy Horse initialized");
}

rule crazyHorseRunningFight
inactive
minInterval 65
{
   llLogRuleTick("crazyHorseRunningFight");
   if (gCrazyHorseRulesEnabled == false)
   {
      xsDisableSelf();
      return;
   }

   if (kbGetAge() >= cAge2)
   {
      btBiasCav = 0.8;
      btOffenseDefense = 0.9;
   }
}

void enableLeaderCrazyHorseRules(void)
{
   if (gCrazyHorseRulesEnabled == false)
   {
      return;
   }

   xsEnableRule("crazyHorseRunningFight");
}