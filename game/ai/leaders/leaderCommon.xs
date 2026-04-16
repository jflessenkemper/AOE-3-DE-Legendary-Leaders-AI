//==============================================================================
/* leaderCommon.xs

   Shared helper functions for Legendary Leaders personalities.
*/
//==============================================================================

void llResetLeaderBiases(void)
{
   btRushBoom = 0.0;
   btOffenseDefense = 0.0;
   btBiasNative = 0.0;
   btBiasTrade = 0.0;
   btBiasCav = 0.0;
   btBiasArt = 0.0;
   btBiasInf = 0.0;
}

void llSetBalancedPersonality(void)
{
   llResetLeaderBiases();
   btRushBoom = 0.0;
   btOffenseDefense = 0.0;
}

void llSetAggressivePersonality(void)
{
   llResetLeaderBiases();
   btRushBoom = 0.8;
   btOffenseDefense = 0.8;
}

void llSetDefensivePersonality(void)
{
   llResetLeaderBiases();
   btRushBoom = -0.4;
   btOffenseDefense = -0.6;
}

void llSetMilitaryFocus(float infantryBias = 0.0, float cavalryBias = 0.0, float artilleryBias = 0.0)
{
   btBiasInf = infantryBias;
   btBiasCav = cavalryBias;
   btBiasArt = artilleryBias;
}

void llEnableForwardBaseStyle(void)
{
   btOffenseDefense = 1.0;
   cvDefenseReflexRadiusActive = 75.0;
   cvDefenseReflexSearchRadius = 75.0;
}

void llEnableDeepDefenseStyle(void)
{
   btOffenseDefense = -0.5;
   cvMaxTowers = 7;
   cvDefenseReflexRadiusPassive = 40.0;
}
