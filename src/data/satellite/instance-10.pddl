(define (problem satellite-2sat-3inst)
  (:domain satellite)
  (:objects
    sat1 sat2 - satellite
    inst1 inst2 inst3 - instrument
    image1 spectrograph2 thermograph0 - mode
    star0 star1 phen6 phen8 phen14 phen16 - direction)
  (:init
    (supports inst1 image1)
    (supports inst1 thermograph0)
    (supports inst2 spectrograph2)
    (supports inst3 thermograph0)
    (calibration_target inst1 star0)
    (calibration_target inst2 star1)
    (calibration_target inst3 star0)
    (on_board inst1 sat1)
    (on_board inst2 sat1)
    (on_board inst3 sat2)
    (power_avail sat1)
    (power_avail sat2)
    (pointing sat1 phen6)
    (pointing sat2 phen8))
  (:goal (and (have_image phen6 image1)
              (have_image phen8 spectrograph2)
              (have_image phen14 thermograph0)
              (have_image phen16 thermograph0)))
)
