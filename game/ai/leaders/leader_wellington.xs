//==============================================================================
/* leader_wellington.xs */
//==============================================================================

bool gWellingtonRulesEnabled = false;

void initLeaderWellington(void)
{
   aiEcho("Legendary Leaders: activating Duke of Wellington personality.");

   llSetDefensivePersonality();
   btRushBoom = -0.3;
   btBiasTrade = -0.2;
   btBiasNative = -0.2;
   llSetMilitaryFocus(0.7, -0.2, 0.2);
   llEnableDeepDefenseStyle();
   cvOkToBuildForts = true;
   llSetPrisonerDoctrine(cLLPrisonerDoctrineStrictImprisonment, 0.25, 58.0);
   llEnablePrisonerSystem();
   gWellingtonRulesEnabled = true;
}

rule wellingtonLineDiscipline
inactive
minInterval 75
{
   if (gWellingtonRulesEnabled == false)
   {
      xsDisableSelf();
      return;
   }

   if (kbGetAge() >= cAge3)
   {
      btBiasInf = 0.8;
      btBiasArt = 0.3;
   }
}

void enableLeaderWellingtonRules(void)
{
   if (gWellingtonRulesEnabled == false)
   {
      return;
   }
   xsEnableRule("wellingtonLineDiscipline");
}
