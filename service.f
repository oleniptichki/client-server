      program service
      IMPLICIT NONE
      real temp

      OPEN(40,FILE='temp.dat',STATUS='OLD',ACCESS='DIRECT',
     &   FORM='UNFORMATTED',RECL=4)
      READ(40,REC=1) temp
      write(*,*) temp
      CLOSE(40)
      END
