/* Fixed-memory C port of the exact Calibrator.update/alert numerical rules
 * from original acr_mcr_v2.py (not the whole ACR-MCR optimizer).
 * No physical calibration or learning-performance claim is implied. */
#ifndef ACR_EMBEDDED_ACI_H
#define ACR_EMBEDDED_ACI_H
#include <stdint.h>
#define ACR_ACI_WINDOW 512u
#define ACR_ACI_RECENT 5u
#define ACR_ACI_POINT 0u
#define ACR_ACI_ADAPTIVE 1u
#define ACR_ACI_FROZEN 2u
typedef struct {
  double alpha[2];
  double q[2];
  double scores[ACR_ACI_WINDOW][2];
  double recent[ACR_ACI_RECENT][2];
  unsigned n_scores;
  unsigned n_recent;
  unsigned mode;
} ACR_ACI;
void acr_aci_init(ACR_ACI *state,unsigned mode);
void acr_aci_update(ACR_ACI *state, const double *scores_flat,
                    const uint8_t *covered_flat,unsigned n_rows,unsigned round);
int acr_aci_alert(const ACR_ACI *state);
#endif
