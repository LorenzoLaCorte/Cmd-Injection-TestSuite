<?php

$input = $_GET['input'];

system("find . -name ".escapeshellarg($input));
