#        border1  border2  border3   border4
RAM_0 = [500    ,-1200   ,1100      ,800]
ATC_0 = [0,0,0,0] # initial ATC for every border is 0

max_ATC = 1500 # Assumed value ...........not applicable every time
# If you don't have this value then keep max_ATC = 0

#       CNEC1  CNEC2  CNEC3
PTDF = [[0.2 , 0.3  , 0.1],  # <--border1
        [0.25, 0.35 , 0.15], # <--border2
        [0.2 , 0.4  , 0.1],  # <--border3
        [0.2 , 0.4  , 0.1]]  # <--border4
if len(RAM_0) == len(PTDF) and len(ATC_0) == len(PTDF):
    RAM_positive = []
    RAM_negative = []
    PTDF_positive = []
    PTDF_negative = []
    ATC_positive = []
    ATC_negative = []

    ######################## FOR POSITIVE RAM ############################
    for i in range(0,len(RAM_0)):
        if RAM_0[i] > 0:
            RAM_positive.append(RAM_0[i])
            PTDF_positive.append(PTDF[i])
            ATC_positive.append(ATC_0[i])
        else:
            RAM_negative.append(RAM_0[i])
            PTDF_negative.append(PTDF[i])
            ATC_negative.append(ATC_0[i])

    difference = 1.0
    while difference > 0.001: # 1 KW = 0.001 MW
        ########Step 1 Calculate the Remaining Available Margin################
        RAM_step1 = []
        mul = 0
        for i in range(0, len(RAM_positive)):
            for j in range(0 , len(PTDF_positive[i])):
                mul = mul + PTDF_positive[i][j] * ATC_0[i]
            RAM = RAM_positive[i] - mul
            RAM_step1.append(RAM)
            mul = 0
        # Output of this step is RAM_step1
        ######## End of step 1 #################

        ########## Step 2 Distribute remaining RAM equally among borders ###########
        RAM_shared = []

        for i in range(0,len(RAM_step1)):
            RAM_shared.append(RAM_step1[i]/len(RAM_0))

        # Output of this step is RAM_shared
        ####### End of step 2 #############

        ####### Step 3 Compute additional exchanges #########

        RAM_additional = []
        RAM_additional_min = []
        RAM_additional_child = []
        for i in range(0 , len(RAM_shared)):
            for j in range(0,len(PTDF_positive[i])):
                RAM_additional_child.append(RAM_shared[i]/PTDF_positive[i][j])
            RAM_additional_min.append(min(RAM_additional_child))
            RAM_additional.append(RAM_additional_child)
            RAM_additional_child = []

        # Output of this step is RAM_additional_min
        ####### End of step 3 ############

        #### Step 4 - Find the minimum additional exchange per border and update ATC #########
        changed_ATC = []
        for i in range(0,len(ATC_positive)):
            changed_ATC.append(ATC_positive[i] + RAM_additional_min[i])


        # Output of this step is changed_ATC
        ##### End of step 4 ########


        ##### Step 5 Limit ATC to a predefined max value (if applicable) ##########

        # Let's Assume that the max ATC value is 1500 MW (It is provided by TSO)
        if max_ATC > 0 :
            final_changed_ATC = []
            for i in range(0,len(changed_ATC)):
                final_changed_ATC.append(min(changed_ATC[i],max_ATC))
        else:
            final_changed_ATC = changed_ATC

        # Output of this Step is final_changed_ATC
        ##### End of step 5 ###########


        ####### Step 6 Check Stopping condition :#########
        # If the sum of changes between iteration is less than 1 KW or 0.001 MW
        sum_of_final_changed_ATC = 0
        sum_of_previous_ATC = 0

        for i in range(0,len(final_changed_ATC)):
            sum_of_final_changed_ATC = sum_of_final_changed_ATC + final_changed_ATC[i]

        for i in range(0,len(ATC_0)):
            sum_of_previous_ATC = sum_of_previous_ATC + ATC_0[i]

        difference = sum_of_final_changed_ATC - sum_of_previous_ATC

        ATC_0 = final_changed_ATC
    final_ATC_positive = []
    for i in range(0,len(ATC_0)):
        final_ATC_positive.append(round(ATC_0[i]))
        #######End of step 6 ############



    ##############   End of positive RAM    ###############################


    ################## For Negative RAM ###############################

    ################ Step 1 Calculate the denominator of the ATC formula ##################
    # RAM_negative = []
    # PTDF_negative = []
    # ATC_negative = []

    square_sum_list = []
    square_sum = 0
    for i in range(0,len(PTDF_negative)):
        for j in range(0,len(PTDF_negative[i])):
            square_sum = square_sum + PTDF_negative[i][j]
        square_sum_list.append(square_sum)
    # Output of this step is square_sum_list
    ################ End of Step 1 #####################################

    ################## Step 2 Calculate ATC For each CNEC of each border #############
    CNEC_matrix = []
    border_matrix = []
    border_matrix_min = []
    for i in range(0,len(PTDF_negative)):
        for j in range(0,len(PTDF_negative[i])):
            CNEC_matrix.append((PTDF_negative[i][j] / square_sum_list[i]) * RAM_negative[i])
        border_matrix.append(CNEC_matrix)
        border_matrix_min.append(min(CNEC_matrix))
        CNEC_matrix = []

    # Output of this step is border_matrix_min

    ############## End of step 2 ######################

    ####################### Step 3 Compute Sacling factor for each CNEC ##############
    SF_list = [] # list for scaling factor
    sum = 0
    for i in range(0,len(PTDF_negative)):
        for j in range(0 , len(PTDF_negative[i])):
            sum = sum + PTDF_negative[i][j] * border_matrix_min[i]
        SF_list.append(RAM_negative[i]/sum)
        sum = 0

    # Output of this step is SF_list

    ##################### End of step 3 ################################


    ####################### Step 4 Compute the final Negative ATC ########################
    final_ATC_neagtive = []
    for i in range(0,len(border_matrix_min)):
        final_ATC_neagtive.append(round(border_matrix_min[i] * SF_list[i]))
    ###################  End of Step 4 #############################


    ########################  End of Negative ATC   ###################################

    ################# Final Step : take the minimum of positive and negative ATC ###############
    merged_ATC = []

    for i in range(0,len(final_ATC_positive)):
        merged_ATC.append(final_ATC_positive[i])

    for i in range(0,len(final_ATC_neagtive)):
        merged_ATC.append(final_ATC_neagtive[i])

    final_ATC = min(merged_ATC)

    print(f"The list of positive ATCs : {final_ATC_positive} MW")
    print(f"The list of negative ATCs : {final_ATC_neagtive} MW")
    print(f"The merged list of positive and negative ATC : {merged_ATC} MW")
    print(f"The final ATC is {final_ATC} MW")


    ############## End of Final step #####################################

else:
    print(f"Error!!!\nLength of  RAM matrix is {len(RAM_0)}\nLength of PTDF matrix is {len(PTDF)}\nLength of ATC matrix is {len(ATC_0)}\nLegth of all these matrix should be same")


















