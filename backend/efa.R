args <- commandArgs(trailingOnly=TRUE)
suppressPackageStartupMessages(library(psych))
suppressPackageStartupMessages(library(GPArotation))
suppressPackageStartupMessages(library(jsonlite))
cfg <- fromJSON(args[1]); X <- as.matrix(read.csv(cfg$data,check.names=FALSE))
set.seed(cfg$seed)
options(mc.cores=1)
R <- cor(X)
if(min(eigen(R,symmetric=TRUE)$values)<=1e-10) stop('Matriks korelasi tidak positive definite.')
q <- cfg$q
parallel <- NULL
if(is.null(q)) {
  capture.output(pa <- fa.parallel(X,fa='fa',fm=cfg$extraction,n.iter=500,quant=.95,plot=FALSE),file=NULL)
  q <- pa$nfact
  p <- ncol(X)
  simulation_columns <- (ncol(pa$values)-p+1):ncol(pa$values)
  boundary <- apply(pa$values[,simulation_columns,drop=FALSE],2,quantile,probs=.95)
  parallel <- list(observed=pa$fa.values,simulated=boundary,simulation_mean=pa$fa.sim,n_iter=500,quantile=.95,recommended=q,comparison='95th percentile of simulated common-factor eigenvalues')
}
if(q<1 || q>=ncol(X)) stop('Tidak ada faktor yang didukung atau jumlah faktor tidak sah.')
df <- ncol(X)*(ncol(X)-1)/2-ncol(X)*q+q*(q-1)/2
if(df<0) stop('Model faktor overspecified.')
warnings <- character()
fit <- withCallingHandlers(fa(X,nfactors=q,fm=cfg$extraction,rotate=cfg$rotation,
  scores='regression',use='complete',smooth=FALSE,impute='none',max.iter=1000),
  warning=function(w){warnings <<- c(warnings,conditionMessage(w));invokeRestart('muffleWarning')})
L <- unclass(fit$loadings); Phi <- fit$Phi
if(is.null(Phi)) Phi <- diag(q)
h <- diag(L %*% Phi %*% t(L)); u <- diag(R)-h
if(any(!is.finite(L)) || any(u<=0) || identical(fit$converged,FALSE) || any(grepl('converg|Heywood',warnings,ignore.case=TRUE))) stop('Solusi faktor tidak layak atau tidak konvergen.')
kmo <- KMO(R); bart <- cortest.bartlett(R,n=nrow(X))
result <- list(pattern=L,Phi=Phi,structure=L %*% Phi,communalities=h,uniqueness=u,
 residual=R-(L %*% Phi %*% t(L)+diag(u)),scores=fit$scores,q=q,
 kmo=kmo$MSA,msa=kmo$MSAi,bartlett=bart,parallel=parallel,warnings=warnings,
 versions=list(R=R.version.string,psych=as.character(packageVersion('psych')),GPArotation=as.character(packageVersion('GPArotation'))))
write_json(result,args[2],auto_unbox=TRUE,matrix='rowmajor',digits=NA,null='null')
