# DocumentsLoader

## Performance testing

DocumentsLoader class has been tested using two implementations:
- sequential processing
  ```python
  from __future__ import annotations

  import os
  from pathlib import Path
  from typing import Generator

  from mlclient.model import Document
  
  @classmethod
  def load(
      cls,
      path: str,
      uri_prefix: str = "",
      raw: bool = True,
  ) -> Generator[Document]:
      for dir_path, _, file_names in os.walk(path):
          for file_name in file_names:
              if file_name.endswith(cls._METADATA_SUFFIXES):
                  continue

              file_path = str(Path(dir_path) / file_name)
              uri = file_path.replace(path, uri_prefix)
              yield cls._load_document(file_path, uri, raw)
  ```

- parallel processing
  ```python
  from __future__ import annotations
  
  import os
  from concurrent.futures import ThreadPoolExecutor, as_completed
  from pathlib import Path
  from typing import Generator
  
  from mlclient.model import Document
  
  @classmethod
  def load(
      cls,
      path: str,
      uri_prefix: str = "",
      raw: bool = True,
      thread_count: int = 4,
  ) -> Generator[Document]:
      futures = []
      with ThreadPoolExecutor(
          max_workers=thread_count,
          thread_name_prefix="load_documents_to_memory",
      ) as executor:
          for dir_path, _, file_names in os.walk(path):
              for file_name in file_names:
                  if file_name.endswith(cls._METADATA_SUFFIXES):
                      continue
  
                  file_path = str(Path(dir_path) / file_name)
                  uri = file_path.replace(path, uri_prefix)
                  future = executor.submit(cls._load_document, file_path, uri, raw)
                  futures.append(future)
  
      for future in as_completed(futures):
          yield future.result()
  ```

### Sequential processing results

```text
============================= test session starts ==============================
platform linux -- Python 3.8.10, pytest-7.4.3, pluggy-1.3.0
benchmark: 4.0.0 (defaults: timer=time.perf_counter disable_gc=False min_rounds=5 min_time=0.000005 max_time=1.0 calibration_precision=10 warmup=False warmup_iterations=100000)
rootdir: /home/tom/workspace/projects/mlclient
configfile: pyproject.toml
plugins: mock-3.12.0, benchmark-4.0.0, bdd-7.0.1, cov-4.1.0
collected 8 items

tests/performance/mlclient/jobs/test_documents_loader.py ........        [100%]


------------------------------------------------------------------------------------------------------------------- benchmark: 8 tests ------------------------------------------------------------------------------------------------------------------
Name (time in us)                                    Min                        Max                       Mean                  StdDev                     Median                       IQR            Outliers         OPS            Rounds  Iterations
---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
test_load_and_parse_5_documents                 585.1280 (1.0)             907.4540 (1.38)            623.0043 (1.0)           29.7178 (2.71)            619.8950 (1.0)             19.8120 (1.34)       100;74  1,605.1255 (1.0)        1499           1
test_load_5_documents                           617.2480 (1.05)            659.5520 (1.0)             637.9822 (1.02)          10.9607 (1.0)             635.4090 (1.03)            14.7843 (1.0)           7;0  1,567.4418 (0.98)         19           1
test_load_500_documents                      61,523.1510 (105.14)       81,268.2060 (123.22)       69,769.5609 (111.99)     6,419.6223 (585.70)       69,299.1290 (111.79)      10,830.1285 (732.54)        6;0     14.3329 (0.01)         17           1
test_load_and_parse_500_documents            71,846.7640 (122.79)       72,714.4500 (110.25)       72,256.4896 (115.98)       294.8808 (26.90)        72,267.7000 (116.58)         567.8920 (38.41)         6;0     13.8396 (0.01)         14           1
test_load_and_parse_15000_documents       1,840,720.2510 (>1000.0)   2,036,604.5860 (>1000.0)   1,891,858.0868 (>1000.0)   82,669.8488 (>1000.0)   1,849,863.0060 (>1000.0)     76,528.2625 (>1000.0)       1;0      0.5286 (0.00)          5           1
test_load_15000_documents                 1,998,823.6960 (>1000.0)   2,184,843.4250 (>1000.0)   2,061,938.6152 (>1000.0)   85,767.6382 (>1000.0)   2,004,440.7540 (>1000.0)    135,414.7990 (>1000.0)       1;0      0.4850 (0.00)          5           1
test_load_and_parse_200000_documents     20,544,330.9490 (>1000.0)  22,805,081.9720 (>1000.0)  21,428,071.4656 (>1000.0)  927,977.5251 (>1000.0)  20,988,211.1030 (>1000.0)  1,367,730.1472 (>1000.0)       1;0      0.0467 (0.00)          5           1
test_load_200000_documents               21,273,517.3620 (>1000.0)  21,764,147.0820 (>1000.0)  21,472,532.9390 (>1000.0)  180,037.4190 (>1000.0)  21,429,811.2930 (>1000.0)    169,361.2740 (>1000.0)       2;0      0.0466 (0.00)          5           1
---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

Legend:
  Outliers: 1 Standard Deviation from Mean; 1.5 IQR (InterQuartile Range) from 1st Quartile and 3rd Quartile.
  OPS: Operations Per Second, computed as 1 / Mean
======================== 8 passed in 335.67s (0:05:35) =========================
```

### Parallel processing results

#### 4 threads

```text
============================= test session starts ==============================
platform linux -- Python 3.8.10, pytest-7.4.3, pluggy-1.3.0
benchmark: 4.0.0 (defaults: timer=time.perf_counter disable_gc=False min_rounds=5 min_time=0.000005 max_time=1.0 calibration_precision=10 warmup=False warmup_iterations=100000)
rootdir: /home/tom/workspace/projects/mlclient
configfile: pyproject.toml
plugins: mock-3.12.0, benchmark-4.0.0, bdd-7.0.1, cov-4.1.0
collected 8 items

tests/performance/mlclient/jobs/test_documents_loader.py ........        [100%]


----------------------------------------------------------------------------------------------------------------- benchmark: 8 tests ----------------------------------------------------------------------------------------------------------------
Name (time in us)                                    Min                        Max                       Mean                  StdDev                     Median                     IQR            Outliers       OPS            Rounds  Iterations
-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
test_load_and_parse_5_documents                 938.2150 (1.0)           1,626.3460 (1.0)           1,116.0278 (1.0)           86.7650 (1.0)           1,127.1850 (1.0)          139.6710 (1.0)         336;1  896.0350 (1.0)         910           1
test_load_5_documents                         1,201.7820 (1.28)          2,421.0030 (1.49)          1,792.7842 (1.61)         523.0486 (6.03)          1,657.9660 (1.47)         911.7383 (6.53)          2;0  557.7916 (0.62)          5           1
test_load_500_documents                      76,381.9350 (81.41)       104,944.7130 (64.53)        84,127.1069 (75.38)      7,763.5160 (89.48)        82,664.8690 (73.34)      7,954.7390 (56.95)         1;1   11.8868 (0.01)         12           1
test_load_and_parse_500_documents            78,766.6720 (83.95)        99,227.1450 (61.01)        88,046.8478 (78.89)      6,201.6478 (71.48)        86,537.1035 (76.77)     10,388.5840 (74.38)         3;0   11.3576 (0.01)         10           1
test_load_15000_documents                 2,490,487.6220 (>1000.0)   2,705,933.3240 (>1000.0)   2,606,668.0710 (>1000.0)   76,914.3567 (886.47)    2,611,796.3530 (>1000.0)   69,450.6390 (497.24)        2;0    0.3836 (0.00)          5           1
test_load_and_parse_15000_documents       2,579,229.6630 (>1000.0)   2,646,320.3280 (>1000.0)   2,614,369.9480 (>1000.0)   29,721.7296 (342.55)    2,608,391.2020 (>1000.0)   53,516.2515 (383.16)        2;0    0.3825 (0.00)          5           1
test_load_200000_documents               32,243,641.1750 (>1000.0)  34,613,497.6780 (>1000.0)  33,511,721.9326 (>1000.0)  846,956.4541 (>1000.0)  33,636,080.6050 (>1000.0)  779,385.7715 (>1000.0)       2;0    0.0298 (0.00)          5           1
test_load_and_parse_200000_documents     32,817,093.9130 (>1000.0)  35,015,985.9400 (>1000.0)  33,617,483.8536 (>1000.0)  840,233.2814 (>1000.0)  33,507,876.3770 (>1000.0)  878,704.7107 (>1000.0)       1;0    0.0297 (0.00)          5           1
-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

Legend:
  Outliers: 1 Standard Deviation from Mean; 1.5 IQR (InterQuartile Range) from 1st Quartile and 3rd Quartile.
  OPS: Operations Per Second, computed as 1 / Mean
======================== 8 passed in 513.46s (0:08:33) =========================
```

#### 8 threads

```text
============================= test session starts ==============================
platform linux -- Python 3.8.10, pytest-7.4.3, pluggy-1.3.0
benchmark: 4.0.0 (defaults: timer=time.perf_counter disable_gc=False min_rounds=5 min_time=0.000005 max_time=1.0 calibration_precision=10 warmup=False warmup_iterations=100000)
rootdir: /home/tom/workspace/projects/mlclient
configfile: pyproject.toml
plugins: mock-3.12.0, benchmark-4.0.0, bdd-7.0.1, cov-4.1.0
collected 8 items

tests/performance/mlclient/jobs/test_documents_loader.py ........        [100%]


----------------------------------------------------------------------------------------------------------------- benchmark: 8 tests ----------------------------------------------------------------------------------------------------------------
Name (time in us)                                    Min                        Max                       Mean                  StdDev                     Median                     IQR            Outliers       OPS            Rounds  Iterations
-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
test_load_and_parse_5_documents                 941.1140 (1.0)          10,368.7250 (5.72)          1,577.9836 (1.21)         565.1217 (1.83)          1,556.0160 (1.21)         498.4515 (1.37)        72;28  633.7201 (0.83)        904           1
test_load_5_documents                         1,024.9550 (1.09)          1,813.3740 (1.0)           1,307.4064 (1.0)          308.7377 (1.0)           1,284.0510 (1.0)          364.5287 (1.0)           1;0  764.8731 (1.0)           5           1
test_load_500_documents                     110,005.1300 (116.89)      140,437.1210 (77.45)       124,294.1573 (95.07)     11,915.3484 (38.59)       122,521.0580 (95.42)     22,936.7105 (62.92)         3;0    8.0454 (0.01)          9           1
test_load_and_parse_500_documents           132,031.9400 (140.29)      157,669.8330 (86.95)       137,975.4701 (105.53)     8,325.5999 (26.97)       135,863.4710 (105.81)     5,426.3380 (14.89)         1;1    7.2477 (0.01)          8           1
test_load_and_parse_15000_documents       2,819,385.7740 (>1000.0)   3,447,328.8330 (>1000.0)   3,037,987.7282 (>1000.0)  257,023.6670 (832.50)    3,028,316.9790 (>1000.0)  347,937.8880 (954.49)        1;0    0.3292 (0.00)          5           1
test_load_15000_documents                 3,399,094.0100 (>1000.0)   3,953,992.9210 (>1000.0)   3,723,663.3764 (>1000.0)  217,371.2835 (704.06)    3,723,592.5830 (>1000.0)  310,266.2248 (851.14)        2;0    0.2686 (0.00)          5           1
test_load_and_parse_200000_documents     39,141,543.5580 (>1000.0)  39,911,091.0840 (>1000.0)  39,520,193.9362 (>1000.0)  304,445.0770 (986.10)   39,441,853.9760 (>1000.0)  465,389.4082 (>1000.0)       2;0    0.0253 (0.00)          5           1
test_load_200000_documents               39,338,956.0140 (>1000.0)  40,415,255.0200 (>1000.0)  39,659,359.0542 (>1000.0)  438,734.3184 (>1000.0)  39,556,489.5350 (>1000.0)  452,826.5455 (>1000.0)       1;0    0.0252 (0.00)          5           1
-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

Legend:
  Outliers: 1 Standard Deviation from Mean; 1.5 IQR (InterQuartile Range) from 1st Quartile and 3rd Quartile.
  OPS: Operations Per Second, computed as 1 / Mean
======================== 8 passed in 609.93s (0:10:09) =========================
```

#### 12 threads

```text
============================= test session starts ==============================
platform linux -- Python 3.8.10, pytest-7.4.3, pluggy-1.3.0
benchmark: 4.0.0 (defaults: timer=time.perf_counter disable_gc=False min_rounds=5 min_time=0.000005 max_time=1.0 calibration_precision=10 warmup=False warmup_iterations=100000)
rootdir: /home/tom/workspace/projects/mlclient
configfile: pyproject.toml
plugins: mock-3.12.0, benchmark-4.0.0, bdd-7.0.1, cov-4.1.0
collected 8 items

tests/performance/mlclient/jobs/test_documents_loader.py ........        [100%]


------------------------------------------------------------------------------------------------------------------- benchmark: 8 tests ------------------------------------------------------------------------------------------------------------------
Name (time in us)                                    Min                        Max                       Mean                    StdDev                     Median                       IQR            Outliers       OPS            Rounds  Iterations
---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
test_load_and_parse_5_documents                 947.8710 (1.0)           2,598.6350 (1.17)          1,253.0732 (1.0)            219.5286 (1.0)           1,193.0660 (1.0)            150.3417 (1.0)        129;86  798.0380 (1.0)         933           1
test_load_5_documents                         1,209.1070 (1.28)          2,215.2560 (1.0)           1,745.6008 (1.39)           447.6031 (2.04)          1,911.2770 (1.60)           793.0553 (5.28)          2;0  572.8687 (0.72)          5           1
test_load_500_documents                      89,407.6920 (94.32)       233,526.9490 (105.42)      114,807.1061 (91.62)       41,409.4340 (188.63)       96,588.3480 (80.96)       34,726.1470 (230.98)        1;1    8.7103 (0.01)         12           1
test_load_and_parse_500_documents            89,583.2090 (94.51)       158,664.8710 (71.62)       121,032.7976 (96.59)       24,817.7279 (113.05)      120,253.1865 (100.79)      38,601.5610 (256.76)        2;0    8.2622 (0.01)          8           1
test_load_and_parse_15000_documents       2,939,816.6250 (>1000.0)   3,248,407.5410 (>1000.0)   3,054,482.0122 (>1000.0)    115,508.1185 (526.16)    3,035,461.0420 (>1000.0)     99,321.9673 (660.64)        1;1    0.3274 (0.00)          5           1
test_load_15000_documents                 3,292,936.7960 (>1000.0)   3,572,910.4150 (>1000.0)   3,436,345.4510 (>1000.0)    115,005.0311 (523.87)    3,437,134.7560 (>1000.0)    194,002.8883 (>1000.0)       2;0    0.2910 (0.00)          5           1
test_load_and_parse_200000_documents     40,155,542.8370 (>1000.0)  41,459,742.3180 (>1000.0)  40,688,039.4702 (>1000.0)    490,739.5558 (>1000.0)  40,710,378.7910 (>1000.0)    562,082.4325 (>1000.0)       2;0    0.0246 (0.00)          5           1
test_load_200000_documents               41,995,291.6750 (>1000.0)  44,739,186.1600 (>1000.0)  42,802,439.5304 (>1000.0)  1,192,556.2163 (>1000.0)  42,054,522.4500 (>1000.0)  1,543,775.4330 (>1000.0)       1;0    0.0234 (0.00)          5           1
---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

Legend:
  Outliers: 1 Standard Deviation from Mean; 1.5 IQR (InterQuartile Range) from 1st Quartile and 3rd Quartile.
  OPS: Operations Per Second, computed as 1 / Mean
======================== 8 passed in 633.72s (0:10:33) =========================
```

#### 24 threads

```text
============================= test session starts ==============================
platform linux -- Python 3.8.10, pytest-7.4.3, pluggy-1.3.0
benchmark: 4.0.0 (defaults: timer=time.perf_counter disable_gc=False min_rounds=5 min_time=0.000005 max_time=1.0 calibration_precision=10 warmup=False warmup_iterations=100000)
rootdir: /home/tom/workspace/projects/mlclient
configfile: pyproject.toml
plugins: mock-3.12.0, benchmark-4.0.0, bdd-7.0.1, cov-4.1.0
collected 8 items

tests/performance/mlclient/jobs/test_documents_loader.py ........        [100%]


----------------------------------------------------------------------------------------------------------------- benchmark: 8 tests ----------------------------------------------------------------------------------------------------------------
Name (time in us)                                    Min                        Max                       Mean                  StdDev                     Median                     IQR            Outliers       OPS            Rounds  Iterations
-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
test_load_and_parse_5_documents                 933.1530 (1.0)          30,132.8340 (15.60)         1,509.7135 (1.02)       1,353.7103 (3.14)          1,251.5030 (1.0)          398.6467 (1.0)        40;115  662.3773 (0.98)       1011           1
test_load_5_documents                         1,027.1800 (1.10)          1,931.6350 (1.0)           1,481.0918 (1.0)          430.6741 (1.0)           1,439.1370 (1.15)         835.5165 (2.10)          2;0  675.1776 (1.0)           5           1
test_load_500_documents                      80,020.4350 (85.75)       144,534.9910 (74.83)       104,308.7886 (70.43)     24,443.4654 (56.76)        94,189.3740 (75.26)     34,592.4705 (86.77)         2;0    9.5869 (0.01)          7           1
test_load_and_parse_500_documents            83,762.7860 (89.76)       171,325.4980 (88.69)       117,844.8355 (79.57)     28,124.7978 (65.30)       122,470.8800 (97.86)     38,775.1715 (97.27)         3;0    8.4857 (0.01)         12           1
test_load_15000_documents                 2,973,030.1890 (>1000.0)   3,617,962.1190 (>1000.0)   3,256,854.8792 (>1000.0)  268,053.1885 (622.40)    3,260,738.8440 (>1000.0)  448,094.1435 (>1000.0)       2;0    0.3070 (0.00)          5           1
test_load_and_parse_15000_documents       3,007,220.4230 (>1000.0)   3,442,634.4530 (>1000.0)   3,200,380.7464 (>1000.0)  169,058.1175 (392.54)    3,164,164.2750 (>1000.0)  246,862.7977 (619.25)        2;0    0.3125 (0.00)          5           1
test_load_and_parse_200000_documents     39,352,262.4820 (>1000.0)  39,962,050.0160 (>1000.0)  39,670,848.7124 (>1000.0)  268,267.1456 (622.90)   39,623,362.8870 (>1000.0)  481,962.3377 (>1000.0)       2;0    0.0252 (0.00)          5           1
test_load_200000_documents               39,474,593.6930 (>1000.0)  41,175,477.4300 (>1000.0)  40,274,329.8374 (>1000.0)  612,848.2562 (>1000.0)  40,318,118.0670 (>1000.0)  632,601.4925 (>1000.0)       2;0    0.0248 (0.00)          5           1
-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

Legend:
  Outliers: 1 Standard Deviation from Mean; 1.5 IQR (InterQuartile Range) from 1st Quartile and 3rd Quartile.
  OPS: Operations Per Second, computed as 1 / Mean
======================== 8 passed in 611.34s (0:10:11) =========================
```

## Conclusion

Loading documents into memory is so fast that it costs time to initialize and manage threads with ThreadPoolExecutor.
That's why the sequential processing implementation will be applied.

Interesting is that parsing documents to XMLDocument class is not time-consuming but actually similar to RawDocument
