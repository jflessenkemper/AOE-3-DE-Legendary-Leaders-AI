//==============================================================================
/* leader_isabella.xs */
//==============================================================================

bool gIsabellaRulesEnabled = false;

void initLeaderIsabella(void)
{
   llVerboseEcho("Legendary Leaders: activating Isabella I personality.");

   llSetAggressivePersonality();
   btRushBoom = 0.5;
   btOffenseDefense = 0.8;
   btBiasTrade = -0.5;
   btBiasNative = -0.3;
   llSetMilitaryFocus(0.5, 0.1, 0.2);
   llSetLeaderTacticalDoctrine(0.48, 0.72, 0, -1.0);
   cvMaxTowers = 4;
   llSetPrisonerDoctrine(cLLPrisonerDoctrineExecution, 0.40, 74.0);
   llEnablePrisonerSystem();
   gIsabellaRulesEnabled = true;
   llLogLeaderState("Isabella initialized");
}

rule isabellaCrusadingTempo
inactive
minInterval 75
{
   llLogRuleTick("isabellaCrusadingTempo");
   if (gIsabellaRulesEnabled == false)
   {
      xsDisableSelf();
      return;
   }

   if (kbGetAge() >= cAge2)
   {
      btBiasInf = 0.6;
      btBiasArt = 0.3;
   }
}

void enableLeaderIsabellaRules(void)
{
   if (gIsabellaRulesEnabled == false)
   {
      return;
   }
   xsEnableRule("isabellaCrusadingTempo");
}
