(define (problem satellite-1sat-2images)
  (:domain satellite)
  (:objects
    sat1 - satellite
    inst1 - instrument
    image1 - mode
    star0 phen6 phen8 - direction)
  (:init
    (supports inst1 image1)
    (calibration_target inst1 star0)
    (on_board inst1 sat1)
    (power_avail sat1)
    (pointing sat1 phen6))
  (:goal (and (have_image phen6 image1)
              (have_image phen8 image1)))
)
