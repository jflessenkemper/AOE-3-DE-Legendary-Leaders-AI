//==============================================================================
/* leader_isabella.xs */
//==============================================================================

bool gIsabellaRulesEnabled = false;

void initLeaderIsabella(void)
{
   aiEcho("Legendary Leaders: activating Isabella I personality.");

   llSetAggressivePersonality();
   btRushBoom = 0.5;
   btOffenseDefense = 0.8;
   btBiasTrade = -0.5;
   btBiasNative = -0.3;
   llSetMilitaryFocus(0.5, 0.1, 0.2);
   cvMaxTowers = 4;
   llSetPrisonerDoctrine(cLLPrisonerDoctrineExecution, 0.40, 74.0);
   llEnablePrisonerSystem();
   gIsabellaRulesEnabled = true;
}

rule isabellaCrusadingTempo
inactive
minInterval 75
{
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
