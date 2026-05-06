(define (problem satellite-2sat)
  (:domain satellite)
  (:objects
    sat1 sat2 - satellite
    inst1 inst2 - instrument
    image1 - mode
    star0 phen6 phen8 - direction)
  (:init
    (supports inst1 image1)
    (supports inst2 image1)
    (calibration_target inst1 star0)
    (calibration_target inst2 star0)
    (on_board inst1 sat1)
    (on_board inst2 sat2)
    (power_avail sat1)
    (power_avail sat2)
    (pointing sat1 phen6)
    (pointing sat2 phen8))
  (:goal (and (have_image phen6 image1)
              (have_image phen8 image1)))
)
