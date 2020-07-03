 //Trajectories of 2-D ABC model
//@author  Xiangwen Wang
//@date    2014-02-06
//@version 1.25
#define MPICH_SKIP_MPICXX
#include "mpi.h"

#pragma comment (lib, "mpi.lib")

#include<stdio.h>
#include<math.h>
#include<stdlib.h>
#include<string.h>
#include<time.h>

#define H 100			//height is 2H+1
#define N 3000             //3N is the size of the rings
#define T 2000000	//total processing time
#define T_GAP (3*N*H)	   //every T_GAP steps, calculate the displacements
//#define PROB 0.5		   //This is the q in ABC model


//--------------random number generator-------------------
#define  M  2147483647.0
#define  Q  127773
#define  R  2836
#define  A  16807
#define  NS  200
#define  pi  3.1415927
double  schrage(double  x) { //generate random number between [0,1]
	double  b,c;
	modf(x*M/Q,&c);
	b=A*fmod(x*M,Q)-R*(c);
	if(b<0)b=b+M;
	return(b/M);          
}
//--------------------------16807------------------------------


//------judge function is used to judge if they should swap----
int judge(int pre, int lat){
	if(pre-lat==1||pre-lat==-2) return 1;
	//BA,CB,AC return 1
	else if(lat-pre==1||lat-pre==-2) return -1;
	//AB,BC,CA return -1
	else return 1;
	//AA,BB,CC return 1
}
//-------------------------------judge-------------------------


int abc(int i){
	if(abs(i)<2*N) return 'a';
	else if(abs(i)<4*N) return 'b';
	else return 'c';
}


int swap(int par_1[3], int par_2[3]){
	int temp=0;
	temp=par_1[0];
	par_1[0]=par_2[0];
	par_2[0]=temp;
	temp=par_1[1];
	par_1[1]=par_2[1];
	par_2[1]=temp;
	temp=par_1[2];
	par_1[2]=par_2[2];
	par_2[2]=temp;
	return 1;
}




//----------find the position of a certain particle------------
int position(int rings[3*N], int label){
	long i=0;
	for(i=0;i<3*N;i++){
		if(rings[i]==label) break;
	}
	return i;
}
//-------------position---------------------------------------





int main(int argc, char *argv[]){
	if(argv[1]==NULL) exit(0);

	double prob=0.1;
	prob=strtod(argv[1], NULL);

	double changed_p=prob;
	long change_time=0;
	changed_p=strtod(argv[2], NULL);
	change_time=strtol(argv[3], NULL, 10);
	
/*	
	printf("%f,%f,%ld\n",prob,changed_p,change_time);
	getchar();
	exit(0);
*/	
	
    int myid, numprocs;
    long file_num;
	long count_gap=2*change_time,judge_gap=0;
	double y=0.0;// y is the random number
	long t=0;
	long a=0, b=0, c=0;
	long i=0, j=0, k=0, posi=0, posi_r=0, posi_c=0;// dist=0;
	double total_ch=0, change=0;

	int *pre, *lat;
//	long edge=0,middle=0;
	static int rings[3*N][H][3],label[3*N];
	//rings[][][0] is the label of the particle, 
	//rings[][][1] is the "page" of the particle on x direction, 
	//rings[][][2] is the "page" of the particle on y direction.

	char file_all[64]="";

//	strcat(file_all, argv[1]);
	
	FILE *fp_all;

    MPI_Init(&argc,&argv);
    MPI_Comm_size(MPI_COMM_WORLD,&numprocs);
    MPI_Comm_rank(MPI_COMM_WORLD,&myid);
    file_num=myid;
    
    sprintf(file_all, "%dx%d_%.1lf_%.1lf_%ld_%ld.dat",3*N,H,prob,changed_p,change_time,file_num);
	//---------saving file-----------
	if((fp_all=fopen(file_all,"w"))==NULL)	{
		printf("cannot open file %s\n", file_all);
		exit(0);
	}
	fclose(fp_all);
	//-------------------------------
	
	time_t rawtime;
	time (&rawtime); //get the random seed by time
	y=schrage((rawtime+file_num*2000)/M);


	//-----------initializing-----------------
	for(i=0;i<3*N;i++){
		for(j=0;j<H;j++){ //put the particles into the rings
			y=schrage(y);   //get a new random number
			if(y*3<=1)	rings[i][j][0]=-N;   
			else if(y*3<=2)	rings[i][j][0]=-3*N;
			else	rings[i][j][0]=-5*N;
			rings[i][j][1]=0;
			rings[i][j][2]=0;
		}
	}

	for(i=0;i<3*N;i++){ //put the particles into the rings
		if(abs(rings[i][H/2][0])<2*N){
			a++;
			rings[i][H/2][0]=a;   
			//a b c are the label of each particle.  
			//if the label<=2N, then it is a A particle, similarly 2N<B<4N, and C>4N. 
			//Here use 2N because there may be more than N particles of the similar kind.
		}
		else if(abs(rings[i][H/2][0])<4*N){
			b++;
			rings[i][H/2][0]=b+2*N;
		}
		else{
			c++;
			rings[i][H/2][0]=c+4*N;
		}
		label[i]=rings[i][H/2][0];
	}
	//----------initialized-----------------


	//---Begin aging----
	for(t=1;t<=T;t++){ //aging time. each one represent one try on each particle.
		if(t==change_time) {
            count_gap=10;
            prob=changed_p;
        }
		for(k=0;k<T_GAP;k++){	
			y=schrage(y);
			if(y<=0.5){ //half chance to excuate row swaping	
				y=schrage(y);
				if(y==1) continue;
				posi_r=(int)(y*3*N);
				y=schrage(y);
				if(y==1) continue;
				posi_c=(int)(y*H);
				if(posi_r-(3*N-1)){
					if(judge(abc(rings[posi_r][posi_c][0]),abc(rings[posi_r+1][posi_c][0]))==1){
						//AA, BB, CC, BA, CB, AC swap with probability 1
						pre=&rings[posi_r][posi_c][0];
						lat=&rings[posi_r+1][posi_c][0];
						swap(pre, lat);
					}
					else if(judge(abc(rings[posi_r][posi_c][0]),abc(rings[posi_r+1][posi_c][0]))==-1){
						//AB, BC, CA swap with probability q
						y=schrage(y);
						if(y<=prob){
							pre=&rings[posi_r][posi_c][0];
							lat=&rings[posi_r+1][posi_c][0];
							swap(pre, lat);
						}
					}
					else{}
				}
				else{
	//				edge++;
					if(judge(abc(rings[posi_r][posi_c][0]),abc(rings[0][posi_c][0]))==1){
						//AA, BB, CC, BA, CB, AC swap with probability 1
						pre=&rings[posi_r][posi_c][0];
						lat=&rings[0][posi_c][0];
						swap(pre, lat);
						rings[posi_r][posi_c][1]-=1;
						rings[0][posi_c][1]+=1;
					}
					else if(judge(abc(rings[posi_r][posi_c][0]),abc(rings[0][posi_c][0]))==-1){
						//AB, BC, CA swap with probability q
						y=schrage(y);
						if(y<=prob){
							pre=&rings[posi_r][posi_c][0];
							lat=&rings[0][posi_c][0];
							swap(pre, lat);
							rings[posi_r][posi_c][1]-=1;
							rings[0][posi_c][1]+=1;
						}
					}
					else{}
				}
			}

			else{ //column swaping
				y=schrage(y);
				if(y==1) continue;
				posi_r=(int)(y*3*N);
				y=schrage(y);
				if(y==1) continue;
				posi_c=(int)(y*H);
				if(posi_c-(H-1)){
					if(judge(abc(rings[posi_r][posi_c][0]),abc(rings[posi_r][posi_c+1][0]))==1){
						//BA, CB, AC swap with probability 1
						pre=&rings[posi_r][posi_c][0];
						lat=&rings[posi_r][posi_c+1][0];
						swap(pre, lat);		
					}
					else if(judge(abc(rings[posi_r][posi_c][0]),abc(rings[posi_r][posi_c+1][0]))==-1){
						//AB, BC, CA swap with probability 1
						pre=&rings[posi_r][posi_c][0];
						lat=&rings[posi_r][posi_c+1][0];
						swap(pre, lat);							
					}
					else{}
				}
				else{
					if(judge(abc(rings[posi_r][posi_c][0]),abc(rings[posi_r][0][0]))==1){
						//BA, CB, AC swap with probability 1
						pre=&rings[posi_r][posi_c][0];
						lat=&rings[posi_r][0][0];
						swap(pre,lat);
						rings[posi_r][posi_c][2]--;
						rings[posi_r][0][2]++;
					}
					else if(judge(abc(rings[posi_r][posi_c][0]),abc(rings[posi_r][0][0]))==-1){
						//AB, BC, CA swap with probability 1
						pre=&rings[posi_r][posi_c][0];
						lat=&rings[posi_r][0][0];
						swap(pre,lat);	
						rings[posi_r][posi_c][2]--;
						rings[posi_r][0][2]++;				
					}
					else{}
				}
			}
		}

		//every T_GAP times, record the displacements
		if((t-change_time)&&((t-change_time)%count_gap==0)) judge_gap=1;
		if(judge_gap){
//			printf("edge:%ld\tmiddle:%ld\n", edge ,middle);
//			getchar();
			judge_gap=0;
			count_gap=count_gap*1.2;
			total_ch=0.0;
			for(i=0;i<3*N;i++){
				for(j=0;j<H;j++){
					if(rings[i][j][0]<0) continue;
					posi=position(label, rings[i][j][0]);
					change=i+rings[i][j][1]*3.0*N-posi;
//					printf("%d (%d)  ", change, rings[i][j][1]);
					total_ch=total_ch+fabs(change);
				}
			}
			if((fp_all=fopen(file_all,"a"))==NULL)	 exit(0);
			fprintf(fp_all,"%.0lf\t%lf\n", (double)(t-change_time), total_ch/(3*N));
			fclose(fp_all);
//			getchar();
			//printf("%.0lf\t%lf\n", (double)t, total_ch/(3*N));
			//printf("%.1f,%.1f,%ld\n",prob,changed_p,change_time);
		}
	}
	//---end of aging---
	printf("-------all finished-------------------\n\n");
    MPI_Finalize();
	return 216;
}
