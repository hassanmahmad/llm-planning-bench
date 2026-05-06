(define (problem satellite-1sat-2modes)
  (:domain satellite)
  (:objects
    sat1 - satellite
    inst1 - instrument
    image1 spectrograph2 - mode
    star0 phen6 - direction)
  (:init
    (supports inst1 image1)
    (supports inst1 spectrograph2)
    (calibration_target inst1 star0)
    (on_board inst1 sat1)
    (power_avail sat1)
    (pointing sat1 phen6))
  (:goal (and (have_image phen6 image1)
              (have_image phen6 spectrograph2)))
)
