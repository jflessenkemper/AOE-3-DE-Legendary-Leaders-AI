//==============================================================================
/* leader_pachacuti.xs */
//==============================================================================

bool gPachacutiRulesEnabled = false;

void initLeaderPachacuti(void)
{
   aiEcho("Legendary Leaders: activating Pachacuti personality.");

   llSetDefensivePersonality();
   btRushBoom = -0.2;
   btOffenseDefense = -0.1;
   btBiasTrade = 0.0;
   btBiasNative = 0.4;
   llSetMilitaryFocus(0.7, -0.2, 0.1);
   cvMaxTowers = 6;
   cvOkToBuildForts = true;
   llSetPrisonerDoctrine(cLLPrisonerDoctrineForcedLabor, 0.28, 60.0);
   llEnablePrisonerSystem();
   gPachacutiRulesEnabled = true;
}

rule pachacutiMountainEmpire
inactive
minInterval 85
{
   if (gPachacutiRulesEnabled == false)
   {
      xsDisableSelf();
      return;
   }

   if (kbGetAge() >= cAge3)
   {
      btBiasInf = 0.7;
      cvOkToBuildForts = true;
   }
}

void enableLeaderPachacutiRules(void)
{
   if (gPachacutiRulesEnabled == false)
   {
      return;
   }

   xsEnableRule("pachacutiMountainEmpire");
}